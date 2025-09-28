import os
from pydantic import BaseModel, Field
from genkit.ai import Genkit
from genkit.plugins.google_genai import GoogleAI
from dotenv import load_dotenv

load_dotenv()  # carga GEMINI_API_KEY y otras del .env

# Inicializa Genkit pasando explícitamente la API Key
ai = Genkit(
    plugins=[GoogleAI(api_key=os.getenv("GEMINI_API_KEY"))],
    model='googleai/gemini-2.5-flash'
)

class ReportRequest(BaseModel):
    prompt: str = Field(..., description="Texto para generar el reporte")

class ReportResponse(BaseModel):
    report: str

@ai.flow()
async def generar_reporte(input_data: ReportRequest) -> ReportResponse:
    prompt = f"Genera un reporte basado en: {input_data.prompt}"
    result = await ai.generate(prompt=prompt, output_schema=ReportResponse)
    if not result.output:
        raise ValueError("Error al generar el reporte")
    return result.output
