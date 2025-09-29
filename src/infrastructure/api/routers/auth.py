from typing import Any, Coroutine

from fastapi import APIRouter

from ....domain.models import AuthTokenResponse
from ....application.services import AuthService


router = APIRouter(prefix="/auth", tags=["Autenticación"])
auth_service = AuthService()


@router.get("/get-token", response_model=AuthTokenResponse)
async def get_token(email: str, password: str) -> AuthTokenResponse:
    return await auth_service.generate_authtoken(email, password)
