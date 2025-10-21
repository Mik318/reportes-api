import os
import logging
import json
import re
import asyncio
import time
from typing import List
import unicodedata

from dotenv import load_dotenv
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI

from src.domain.models import ReportRequest, ReportResponse


MAX_CHARS = 1245

load_dotenv()  # carga GEMINI_API_KEY y otras del .env

logger = logging.getLogger(__name__)

# Inicializa Genkit pasando explícitamente la API Key (si existe)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "googleai/gemini-2.5-flash")
if GEMINI_API_KEY:
    ai = Genkit(
        plugins=[GoogleAI(api_key=GEMINI_API_KEY)],
        model=GEMINI_MODEL
    )
else:
    ai = None
    logger.warning("GEMINI_API_KEY no encontrada: se usará generador local de fallback para pruebas")


def extract_report_text(noisy: str) -> str:
    """
    Extrae solo el valor del campo 'report' del patrón text='{"report":"..."}'
    eliminando todos los wrappers y metadata.
    """
    if not noisy:
        return noisy

    logger.debug("extract_report_text - Input: %s...", noisy[:200])  # Mostrar primeros 200 chars

    # 1) Buscar el patrón text='...' o text="..." de forma más robusta
    # Usar una estrategia que busque hasta la coma siguiente después del JSON
    # Capturar cualquier cadena entre comillas después de text= de forma segura
    m = re.search(r"text=(['\"])(.*?)\1", noisy, re.DOTALL)
    if not m:
        # Fallback: buscar contenido hasta la siguiente comilla si el primero falla
        m = re.search(r"text=(['\"])([^'\"]*?)\1", noisy, re.DOTALL)
        if not m:
            logger.debug("No se encontró patrón text='...'")
            return noisy  # Si no encuentra el patrón, devolver tal como está

    # El contenido entre las comillas está en el grupo 2
    inner = m.group(2)
    logger.debug("Contenido extraído del text=: %s...", inner[:100])

    # 2) Des-escapar secuencias JSON (\"report\":\"...\")
    try:
        unescaped = inner.encode('utf-8').decode('unicode_escape')
        logger.debug("Después de des-escape: %s...", unescaped[:100])
    except Exception as e:
        logger.debug("Error en des-escape: %s", e)
        unescaped = inner

    # 3) Intentar parsear como JSON y extraer 'report'
    try:
        parsed = json.loads(unescaped)
        if isinstance(parsed, dict) and "report" in parsed:
            result = str(parsed["report"]).strip()

            # Corregir problemas de doble codificación UTF-8 (Ã³ -> ó, etc.)
            try:
                # Si el texto tiene caracteres mal codificados, intentar corregirlos
                if 'Ã' in result:
                    # Convertir a bytes con latin-1 y luego decodificar como UTF-8
                    corrected = result.encode('latin-1').decode('utf-8')
                    result = corrected
                    logger.debug("Corregido encoding UTF-8: %s...", result[:50])
            except Exception as encoding_error:
                logger.debug("No se pudo corregir encoding: %s", encoding_error)

            logger.debug("JSON parseado exitosamente, report: %s...", result[:50])
            return result
        else:
            logger.debug("JSON parseado pero sin 'report' field o no es dict: %s", type(parsed))
    except Exception as e:
        logger.debug("Error parseando JSON: %s", e)

    # 4) Fallback: extraer con regex "report":"..." usando una captura más permisiva
    m2 = re.search(r'"report"\s*:\s*"([^"]*?)"', unescaped)
    if m2:
        try:
            result = m2.group(1).encode('utf-8').decode('unicode_escape').strip()

            # Corregir problemas de doble codificación UTF-8
            try:
                if 'Ã' in result:
                    result = result.encode('latin-1').decode('utf-8')
                    logger.debug("Regex fallback - corregido encoding: %s...", result[:50])
            except Exception:
                pass

            logger.debug("Regex fallback exitoso: %s...", result[:50])
            return result
        except Exception as e:
            logger.debug("Error en regex fallback des-escape: %s", e)
            result = m2.group(1).strip()

            # Intentar corregir encoding también en este caso
            try:
                if 'Ã' in result:
                    result = result.encode('latin-1').decode('utf-8')
            except Exception:
                pass

            logger.debug("Regex fallback sin des-escape: %s...", result[:50])
            return result
    else:
        logger.debug("No se encontró patrón 'report' con regex")

    # 5) Si no se puede extraer, devolver el contenido del text=
    logger.debug("Devolviendo contenido crudo del text=: %s...", inner[:50])
    return inner.strip()


async def _local_generate_report(actividades: List[str]) -> str:
    """Generador local sencillo para pruebas cuando no hay clave de AI.

    Construye un párrafo conciso a partir de las actividades y lo acorta a MAX_CHARS.
    """
    # Intenta combinar actividades en oraciones
    sentences = []
    for a in actividades:
        text = a.strip()
        if not text:
            continue
        # Asegurar que cada activity termine en punto
        if not text.endswith('.'):
            text = text + '.'
        sentences.append(text)

    if not sentences:
        return ""

    # Construir un párrafo: Intro + actividades combinadas
    intro = "Reporte de actividades:"
    paragraph = intro + " " + " ".join(sentences)
    paragraph = ' '.join(paragraph.split())  # normalizar espacios

    if len(paragraph) <= MAX_CHARS:
        return paragraph

    truncated = paragraph[:MAX_CHARS]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space].rstrip()
    return truncated


@ai.flow() if ai is not None else None
async def generar_reporte(input_data: ReportRequest) -> ReportResponse:
    # Timeout configurable para llamadas a la IA (segundos) — aumentado a 20s por defecto
    timeout = int(os.getenv("GENAI_TIMEOUT", "20"))

    # Si no hay API key, usar generador local (igual que antes)
    if ai is None:
        report = await _local_generate_report(input_data.actividades)
        if not report:
            raise ValueError("Error al generar el reporte (fallback local)")
        return ReportResponse(report=report)

    prompt_lines = "\n".join(f"- {a}" for a in input_data.actividades)

    # rango objetivo: cercano o superior a MAX_CHARS
    min_chars = max(int(MAX_CHARS * 0.9), MAX_CHARS - 50)
    max_target = MAX_CHARS + 300  # permitir algo por encima
    # estimación tokens (aprox 4 chars por token)
    max_output_tokens = max(512, int(max_target / 4))

    # Prompt más conciso y directo para acelerar la respuesta
    prompt = (
        f"Redacta un reporte profesional en primera persona y tiempo pasado basado en estas actividades:\n"
        f"{prompt_lines}\n\n"
        f"Longitud: {min_chars}-{max_target} caracteres.\n"
        f'Responde únicamente: {{"report":"tu_texto_aquí"}}'
    )

    # No usar streaming (evitar Channel/callbacks). Llamar siempre a ai.generate() con retries
    raw_text = None
    start_call = None
    def _normalize_text(s: str) -> str:
        if not isinstance(s, str):
            try:
                s = str(s)
            except Exception:
                s = ''
        try:
            s = unicodedata.normalize('NFC', s)
        except Exception:
            pass
        if 'Ã' in s or 'Â' in s:
            try:
                s = s.encode('latin-1').decode('utf-8')
            except Exception:
                pass
        return s

    def fix_mojibake_and_normalize(s: str) -> str:
        """Intentar corregir mojibake común (latin-1 interpretado como utf-8) y normalizar Unicode.

        - Si detecta secuencias típicas de mojibake ('Ã', 'Â'), intenta re-decodificar desde latin-1.
        - Siempre aplica unicodedata.normalize('NFC').
        """
        if not isinstance(s, str):
            try:
                s = str(s or '')
            except Exception:
                s = ''
        # Primer intento: normalizar
        try:
            s = unicodedata.normalize('NFC', s)
        except Exception:
            pass

        # Si hay indicios de mojibake, intentar re-decode
        if 'Ã' in s or 'Â' in s:
            try:
                s2 = s.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
                # normalizar resultado
                try:
                    s2 = unicodedata.normalize('NFC', s2)
                except Exception:
                    pass
                s = s2
            except Exception:
                # si falla, mantener original
                pass

        return s

    try:
        start_call = time.perf_counter()
        try:
            raw = await asyncio.wait_for(ai.generate(prompt=prompt, model=GEMINI_MODEL), timeout=timeout)
        except TypeError:
            raw = await asyncio.wait_for(ai.generate(prompt=prompt), timeout=timeout)
        elapsed_call = time.perf_counter() - start_call
        logger.debug("AI generate llamada completada en %.2fs (timeout=%ss)", elapsed_call, timeout)
    except asyncio.TimeoutError:
        logger.warning("Primera llamada a AI timeout tras %ss, intentando reintento con timeout doble", timeout)
        try:
            retry_timeout = timeout * 2
            start_call = time.perf_counter()
            try:
                raw = await asyncio.wait_for(ai.generate(prompt=prompt, model=GEMINI_MODEL), timeout=retry_timeout)
            except TypeError:
                raw = await asyncio.wait_for(ai.generate(prompt=prompt), timeout=retry_timeout)
            elapsed_call = time.perf_counter() - start_call
            logger.debug("Reintento AI completado en %.2fs (timeout=%ss)", elapsed_call, retry_timeout)
        except Exception as retry_exc:
            logger.error("Reintento a la IA falló: %s. Usando generador local de fallback.", retry_exc)
            report = await _local_generate_report(input_data.actividades)
            if not report:
                raise ValueError("Error al generar el reporte (fallback local falló)")
            return ReportResponse(report=report)
    except Exception as e:
        logger.warning("Llamada a IA falló: %s. Intentando fallback local.", e)
        report = await _local_generate_report(input_data.actividades)
        if not report:
            raise ValueError("Error al generar el reporte (fallback local falló)")
        return ReportResponse(report=report)

    # Extraer texto del objeto raw
    if hasattr(raw, 'response') and isinstance(raw.response, str):
        raw_text = _normalize_text(raw.response)
    elif hasattr(raw, 'text') and isinstance(raw.text, str):
        raw_text = _normalize_text(raw.text)
    else:
        raw_text = _normalize_text(str(raw))

    # Captura el contenido de la cadena JSON del campo "report", manejando escapes correctamente
    m = re.search(r'"report"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', raw_text, re.DOTALL)
    report_text = None
    if m:
        candidate = m.group(1)
        try:
            # des-escape JSON string
            candidate_unescaped = candidate.encode('utf-8').decode('unicode_escape')
            parsed = {"report": candidate_unescaped}
            report_text = parsed["report"].strip()
        except Exception:
            report_text = candidate.strip()
    else:
        # fallback: intentar parsear cualquier JSON completo en el texto
        try:
            j = json.loads(raw_text)
            if isinstance(j, dict) and "report" in j:
                report_text = str(j["report"]).strip()
        except Exception:
            report_text = raw_text.strip()

    if not report_text:
        logger.error("No se pudo extraer report del resultado AI")
        raise ValueError("Error al generar el reporte")

    # Aplicar corrección de mojibake / normalización de acentos antes de devolver
    try:
        report_text = fix_mojibake_and_normalize(report_text)
    except Exception:
        logger.debug("No se pudo aplicar fix_mojibake_and_normalize; devolviendo texto sin cambios")

    # Calcular tiempo total solo si start_call fue inicializado
    if start_call is not None:
        try:
            total_elapsed = time.perf_counter() - start_call
            logger.debug("Tiempo total generación (desde llamada AI): %.2fs", total_elapsed)
        except Exception:
            pass

    # Si es más corto que el mínimo objetivo, advertir pero devolver (evitar reintentos costosos)
    if len(report_text) < min_chars:
        logger.warning("Reporte generado corto (%d chars) menor que mínimo %d", len(report_text), min_chars)

    # truncado limpio como antes
    if len(report_text) <= MAX_CHARS:
        return ReportResponse(report=report_text)
    truncated = report_text[:MAX_CHARS]
    last_period = truncated.rfind('.')
    last_space = truncated.rfind(' ')
    if last_period > int(MAX_CHARS * 0.9):
        truncated = truncated[:last_period + 1]
    elif last_space > 0:
        truncated = truncated[:last_space].rstrip()
    # también normalizar/tratar truncado final
    try:
        truncated = fix_mojibake_and_normalize(truncated)
    except Exception:
        pass
    return ReportResponse(report=truncated)
