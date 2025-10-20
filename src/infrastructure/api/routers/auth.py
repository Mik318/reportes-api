from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends

from ....application.services import AuthService
from ....domain.models import AuthTokenResponse, LoginRequest, User
from ....domain.errors import InvalidCredentialsError, EmailNotConfirmedError
from ...api.dependencies import jwt_scheme

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
async def create_acount(body: LoginRequest) -> Any:
    """Crear cuenta: recibir email/password en el body JSON para no exponerlos en la URL."""
    return await auth_service.create_account(body.email, body.password)


@router.get("/verify-token", response_model=User)
async def verify_token(user: User = Depends(jwt_scheme)) -> User:
    """Verifica que el token en Authorization: Bearer <token> sea válido y devuelve el User.

    - Si el token es válido devuelve 200 y el modelo User.
    - Si no lo es, `jwt_scheme` ya lanzará HTTPException con 401.
    """
    return user

# Nota: se eliminó `/auth/save-token` porque el proyecto ahora usa exclusivamente
# Authorization: Bearer <token> en el header (sin cookies). Si necesitas un
# endpoint auxiliar para desarrollo que devuelva el token en el body, lo podemos
# agregar, pero no guardará cookies en el servidor.
