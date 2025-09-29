from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    email: str

class ReportRequest(BaseModel):
    prompt: str = Field(..., description="Texto para generar el reporte")

class ReportResponse(BaseModel):
    report: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

