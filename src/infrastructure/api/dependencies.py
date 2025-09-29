from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .repositories.supabase_auth_repository import SupabaseAuthRepository
from ...domain.models import User

class JWTBearer(HTTPBearer):
    def __init__(self):
        super().__init__()
        self.auth_repository = SupabaseAuthRepository()

    async def __call__(self, request: Request) -> User:
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if credentials:
            token = credentials.credentials
            user = self.auth_repository.get_user_from_token(token)
            if not user:
                raise HTTPException(status_code=401, detail="Token inválido")
            return user
        raise HTTPException(status_code=403, detail="Credenciales faltantes")

jwt_scheme = JWTBearer()

