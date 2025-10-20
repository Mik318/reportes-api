import os
import logging
import json
import re
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI
from dotenv import load_dotenv
from typing import List

# Importar modelos desde domain
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
    # Si no hay API key, usar generador local
    if ai is None:
        report = await _local_generate_report(input_data.actividades)
        if not report:
            raise ValueError("Error al generar el reporte (fallback local)")
        return ReportResponse(report=report)

    prompt_lines = "\n".join(f"- {a}" for a in input_data.actividades)
    prompt = (
        f"Genera un reporte formal y conciso basado en las siguientes actividades:\n"
        f"{prompt_lines}\n\n"
        f"El reporte debe tener exactamente {MAX_CHARS} caracteres. "
        f"Devuélvelo como texto plano en un campo llamado 'report', "
        f"en primera persona y en pasado, sin numeración ni metadatos adicionales. "
        f"IMPORTANTE: Asegúrate de que el texto esté completo y no se corte abruptamente."
    )

    report: str | None = None

    # Intento principal: pedir parsing a schema
    try:
        result = await ai.generate(prompt=prompt, output_schema=ReportResponse)
    except Exception as e:
        logger.debug("Error al generar con output_schema: %s", e)
        # Error al parsear/llamar con schema, intentamos un fallback sin schema
        try:
            raw = await ai.generate(prompt=prompt)
        except Exception as e2:
            logger.error("Error al llamar al proveedor AI (fallback): %s", e2)
            raise ValueError("Error al generar el reporte") from e2

        # Extraer texto del objeto raw de forma defensiva
        if hasattr(raw, 'response') and isinstance(raw.response, str):
            report = raw.response.strip()
        elif hasattr(raw, 'text') and isinstance(raw.text, str):
            report = raw.text.strip()
        else:
            # último recurso: string del objeto
            report = str(raw).strip()
    else:
        # Si no hubo excepción, intentar extraer del resultado parseado
        if getattr(result, 'output', None) and getattr(result.output, 'report', None):
            report = result.output.report.strip()
        else:
            # intentar con propiedades crudas si el schema no produjo output
            if getattr(result, 'response', None) and isinstance(result.response, str):
                report = result.response.strip()
            else:
                # fallback a str(result)
                report = str(result).strip()

    if not report:
        # Loggear el resultado completo para depuración antes de fallar
        try:
            logger.error("Generación AI falló, result raw: %s", str(result if 'result' in locals() else raw if 'raw' in locals() else None))
        except Exception:
            logger.exception("Error al imprimir resultado para depuración")
        raise ValueError("Error al generar el reporte")

    # Extraer solo el texto importante del campo 'report'
    report = extract_report_text(report)

    # Truncado más inteligente: solo si supera significativamente el límite
    if len(report) <= MAX_CHARS:
        return ReportResponse(report=report)

    # Si supera el límite, truncar pero intentar cerrar la oración
    truncated = report[:MAX_CHARS]

    # Buscar el último punto, punto y coma, o coma para terminar de forma natural
    last_period = truncated.rfind('.')
    last_semicolon = truncated.rfind(';')
    last_comma = truncated.rfind(',')

    # Usar el último punto si está cerca del final (dentro del último 10% del texto)
    min_acceptable_length = int(MAX_CHARS * 0.9)

    if last_period > min_acceptable_length:
        truncated = truncated[:last_period + 1]
    elif last_semicolon > min_acceptable_length:
        truncated = truncated[:last_semicolon + 1]
    elif last_comma > min_acceptable_length:
        truncated = truncated[:last_comma + 1]
    else:
        # Fallback: cortar en la última palabra completa
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space].rstrip()

    return ReportResponse(report=truncated)