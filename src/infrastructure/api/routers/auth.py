from typing import Any

from fastapi import APIRouter, HTTPException, status

from ....application.services import AuthService
from ....domain.models import AuthTokenResponse, LoginRequest
from ....domain.errors import InvalidCredentialsError, EmailNotConfirmedError

router = APIRouter(prefix="/auth", tags=["Autenticacion"])
auth_service = AuthService()


@router.post("/get-token", response_model=AuthTokenResponse)
async def get_token(body: LoginRequest) -> AuthTokenResponse:
    try:
        return await auth_service.generate_authtoken(body.email, body.password)
    except EmailNotConfirmedError:
        # El email no ha sido confirmado en Supabase
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email no confirmado")
    except InvalidCredentialsError:
        # Credenciales inválidas
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")


@router.post("/create-account", response_model=Any)
async def create_acount(email: str, password: str) -> Any:
    return await auth_service.create_account(email, password)

# Nota: se eliminó `/auth/save-token` porque el proyecto ahora usa exclusivamente
# Authorization: Bearer <token> en el header (sin cookies). Si necesitas un
# endpoint auxiliar para desarrollo que devuelva el token en el body, lo podemos
# agregar, pero no guardará cookies en el servidor.
