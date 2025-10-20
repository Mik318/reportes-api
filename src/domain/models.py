from pydantic import BaseModel, Field
from typing import List


class Token(BaseModel):
    """
    Modelo para el token de autenticación.
    """
    access_token: str
    token_type: str

class User(BaseModel):
    """
    Modelo de usuario del sistema.
    """
    id: str = Field(..., description="Identificador único del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")


class LoginRequest(BaseModel):
    """Modelo para el login (email y password)"""
    email: str = Field(..., description="Correo del usuario")
    password: str = Field(..., description="Contraseña del usuario")


class ReportRequest(BaseModel):
    """
    Solicitud para generar un reporte.
    """
    actividades: List[str] = Field(..., description="Lista de actividades realizadas")


class ReportResponse(BaseModel):
    """
    Respuesta con el reporte generado.
    """
    report: str = Field(..., description="Reporte generado")

class AuthTokenResponse(BaseModel):
    """
    Respuesta con el token de autenticación.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field("bearer", description="Tipo de token de autenticación")