from typing import Optional

from fastapi import HTTPException, status

from ..domain.errors import UserAlreadyExistsError
from ..domain.models import ReportRequest, ReportResponse, AuthTokenResponse, User
from ..genkit_flow import generar_reporte
from ..infrastructure.api.repositories.supabase_auth_repository import SupabaseAuthRepository


class ReportService:
    async def create_report(self, report_request: ReportRequest) -> ReportResponse:
        return await generar_reporte(report_request)


class AuthService:
    async def generate_authtoken(self, email: str, password: str) -> AuthTokenResponse:
        auth_repository = SupabaseAuthRepository()
        access_token = auth_repository.sign_in_with_password(email, password)
        return AuthTokenResponse(access_token=access_token, token_type="bearer")

    async def create_account(self, email: str, password: str) -> Optional[User]:
        try:
            auth_repository = SupabaseAuthRepository()
            existing_user = auth_repository.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            response = auth_repository.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return User(id=response.user.id, email=response.user.email)
        except UserAlreadyExistsError as e:
            # Se atrapa el error de dominio y se traduce a un error HTTP
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
