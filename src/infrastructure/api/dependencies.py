from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .repositories.supabase_auth_repository import SupabaseAuthRepository
from ...domain.models import User

auth_repository = SupabaseAuthRepository()
security = HTTPBearer(auto_error=False)

async def jwt_scheme(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """Acepta token desde Authorization: Bearer <token> (solo header).

    Nota: ya no se aceptan cookies. El frontend debe enviar el token en el header
    Authorization: Bearer <token>.
    """
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    user = auth_repository.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user