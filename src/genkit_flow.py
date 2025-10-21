import os
import logging
import json
import re
import asyncio
import time
from typing import List, Optional

from dotenv import load_dotenv
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI

from src.domain.models import ReportRequest, ReportResponse


MAX_CHARS = 1245

load_dotenv()  # carga GEMINI_API_KEY y otras del .env

logger = logging.getLogger(__name__)

# Inicializa Genkit pasando explícitamente la API Key (si existe)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    ai = Genkit(
        plugins=[GoogleAI(api_key=GEMINI_API_KEY)],
        model='googleai/gemini-2.5-flash'
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

    print(f"DEBUG extract_report_text - Input: {noisy[:200]}...")  # Mostrar primeros 200 chars

    # 1) Buscar el patrón text='...' o text="..." de forma más robusta
    # Usar una estrategia que busque hasta la coma siguiente después del JSON
    m = re.search(r"text=(?:'|\")(\{.*?\})(?:'|\")", noisy, re.DOTALL)
    if not m:
        # Fallback: buscar cualquier contenido después de text= hasta una coma
        m = re.search(r"text=(?:'|\")([^'\"]*?)(?:'|\")", noisy, re.DOTALL)
        if not m:
            print("DEBUG: No se encontró patrón text='...'")
            return noisy  # Si no encuentra el patrón, devolver tal como está

    inner = m.group(1)
    print(f"DEBUG: Contenido extraído del text=: {inner[:100]}...")

    # 2) Des-escapar secuencias JSON (\"report\":\"...\")
    try:
        unescaped = inner.encode('utf-8').decode('unicode_escape')
        print(f"DEBUG: Después de des-escape: {unescaped[:100]}...")
    except Exception as e:
        print(f"DEBUG: Error en des-escape: {e}")
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
                    print(f"DEBUG: Corregido encoding UTF-8: {result[:50]}...")
            except Exception as encoding_error:
                print(f"DEBUG: No se pudo corregir encoding: {encoding_error}")

            print(f"DEBUG: JSON parseado exitosamente, report: {result[:50]}...")
            return result
        else:
            print(f"DEBUG: JSON parseado pero sin 'report' field o no es dict: {type(parsed)}")
    except Exception as e:
        print(f"DEBUG: Error parseando JSON: {e}")

    # 4) Fallback: extraer con regex "report":"..." usando una captura más permisiva
    m2 = re.search(r'"report"\s*:\s*"([^"]*)"', unescaped)
    if m2:
        try:
            result = m2.group(1).encode('utf-8').decode('unicode_escape').strip()

            # Corregir problemas de doble codificación UTF-8
            try:
                if 'Ã' in result:
                    result = result.encode('latin-1').decode('utf-8')
                    print(f"DEBUG: Regex fallback - corregido encoding: {result[:50]}...")
            except Exception:
                pass

            print(f"DEBUG: Regex fallback exitoso: {result[:50]}...")
            return result
        except Exception as e:
            print(f"DEBUG: Error en regex fallback des-escape: {e}")
            result = m2.group(1).strip()

            # Intentar corregir encoding también en este caso
            try:
                if 'Ã' in result:
                    result = result.encode('latin-1').decode('utf-8')
            except Exception:
                pass

            print(f"DEBUG: Regex fallback sin des-escape: {result[:50]}...")
            return result
    else:
        print("DEBUG: No se encontró patrón 'report' con regex")

    # 5) Si no se puede extraer, devolver el contenido del text=
    print(f"DEBUG: Devolviendo contenido crudo del text=: {inner[:50]}...")
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
    # Timeout configurable para llamadas a la IA (segundos)
    timeout = int(os.getenv("GENAI_TIMEOUT", "8"))

    # Si no hay API key, usar generador local (igual que antes)
    if ai is None:
        report = await _local_generate_report(input_data.actividades)
        if not report:
            raise ValueError("Error al generar el reporte (fallback local)")
        return ReportResponse(report=report)

    prompt_lines = "\n".join(f"- {a}" for a in input_data.actividades)
    # Solicitar \"máximo\" en lugar de \"exactamente\" para evitar trabajo extra del modelo
    prompt = (
            f"Genera un reporte formal y conciso basado en las siguientes actividades:\n"
            f"{prompt_lines}\n\n"
            f"Restricciones:\n"
            f"- Máximo {MAX_CHARS} caracteres. Prioriza frases completas; si truncas, corta en el último punto o espacio antes del límite.\n"
            + "- Responde únicamente con un JSON válido con un único campo \"report\" (ej. `{\"report\":\"...\"}`). No añadas nada más.\n"
            + "- Español, primera persona, pasado, sin numeración ni metadatos.\n"
            + "- Oraciones cortas y concisas. Evita ejemplos, explicaciones y prefacios.\n"
            + "- Si no puedes respetar el límite, devuelve la versión truncada más cercana sin pedir reintentos.\n"
            + "- UTF-8, sin markdown ni etiquetas. No uses caracteres adicionales fuera del JSON.\n"
    )

    report: str | None = None
    start = time.perf_counter()

    # Intento principal: usar output_schema pero con timeout
    try:
        try:
            result = await asyncio.wait_for(ai.generate(prompt=prompt, output_schema=ReportResponse), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("AI generate con output_schema excedió timeout de %s s, intentando fallback", timeout)
            raise
    except Exception as e:
        # Si falla (incluyendo timeout), intentar fallback rápido sin schema con timeout
        logger.debug("Error al generar con output_schema: %s", e)
        try:
            raw = await asyncio.wait_for(ai.generate(prompt=prompt), timeout=timeout)
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start
            logger.error("Timeout generando reporte (fallback) después de %.2fs", elapsed)
            raise ValueError("Timeout generando el reporte") from None
        except Exception as e2:
            logger.error("Error al llamar al proveedor AI (fallback): %s", e2)
            raise ValueError("Error al generar el reporte") from e2

        # Extraer texto del objeto raw de forma defensiva
        if hasattr(raw, 'response') and isinstance(raw.response, str):
            report = raw.response.strip()
        elif hasattr(raw, 'text') and isinstance(raw.text, str):
            report = raw.text.strip()
        else:
            report = str(raw).strip()
    else:
        # Si no hubo excepción, intentar extraer del resultado parseado
        if getattr(result, 'output', None) and getattr(result.output, 'report', None):
            report = result.output.report.strip()
        else:
            if getattr(result, 'response', None) and isinstance(result.response, str):
                report = result.response.strip()
            else:
                report = str(result).strip()

    elapsed_total = time.perf_counter() - start
    logger.debug("Tiempo total generar_reporte: %.2fs", elapsed_total)

    if not report:
        try:
            logger.error("Generación AI falló, result raw: %s", str(result if 'result' in locals() else raw if 'raw' in locals() else None))
        except Exception:
            logger.exception("Error al imprimir resultado para depuración")
        raise ValueError("Error al generar el reporte")

    # Extraer solo el texto importante del campo 'report'
    report = extract_report_text(report)

    # Truncado más inteligente como antes
    if len(report) <= MAX_CHARS:
        return ReportResponse(report=report)

    truncated = report[:MAX_CHARS]
    last_period = truncated.rfind('.')
    last_semicolon = truncated.rfind(';')
    last_comma = truncated.rfind(',')
    min_acceptable_length = int(MAX_CHARS * 0.9)

    if last_period > min_acceptable_length:
        truncated = truncated[:last_period + 1]
    elif last_semicolon > min_acceptable_length:
        truncated = truncated[:last_semicolon + 1]
    elif last_comma > min_acceptable_length:
        truncated = truncated[:last_comma + 1]
    else:
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space].rstrip()

    return ReportResponse(report=truncated)