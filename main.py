import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from genkit_flow import generar_reporte, ReportRequest, ReportResponse
from dotenv import load_dotenv

load_dotenv()  # carga variables de entorno desde .env

app = FastAPI(title="API Reportes IA")

# Cliente Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Inicia sesión con un usuario existente
user = supabase.auth.sign_in_with_password({
    "email": "lokilskdij@gmail.com",
    "password": "Passw0rd!"
})

access_token = user.session.access_token
print(access_token)  # ESTE es el JWT válido

# Autenticación JWT
class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request) -> str:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if credentials:
            token = credentials.credentials
            user_data = supabase.auth.get_user(token)
            if not user_data or not user_data.user:
                raise HTTPException(status_code=401, detail="Token inválido")
            return user_data.user
        raise HTTPException(status_code=403, detail="Credenciales faltantes")

jwt_scheme = JWTBearer()

@app.post("/report", response_model=ReportResponse)
async def crear_reporte(data: ReportRequest, user=Depends(jwt_scheme)):
    reporte = await generar_reporte(data)
    return reporte
