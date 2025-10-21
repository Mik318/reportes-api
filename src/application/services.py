from typing import Optional

from fastapi import HTTPException, status

from ..domain.errors import UserAlreadyExistsError, InvalidCredentialsError
from ..domain.models import ReportRequest, ReportResponse, AuthTokenResponse, User
from ..genkit_flow import generar_reporte
from ..infrastructure.api.repositories.supabase_auth_repository import SupabaseAuthRepository


class ReportService:
    async def create_report(self, report_request: ReportRequest) -> ReportResponse:
        return await generar_reporte(report_request)


class AuthService:
    async def generate_authtoken(self, email: str, password: str) -> AuthTokenResponse:
        auth_repository = SupabaseAuthRepository()
        tokens = auth_repository.sign_in_with_password(email, password)
        access = tokens.get('access_token') if isinstance(tokens, dict) else None
        refresh = tokens.get('refresh_token') if isinstance(tokens, dict) else None
        if not access:
            # No se obtuvo token -> credenciales inválidas
            raise InvalidCredentialsError()
        return AuthTokenResponse(access_token=access, token_type="bearer", refresh_token=refresh)

    async def refresh_authtoken(self, refresh_token: str) -> AuthTokenResponse:
        auth_repository = SupabaseAuthRepository()
        tokens = auth_repository.refresh_with_refresh_token(refresh_token)
        access = tokens.get('access_token') if isinstance(tokens, dict) else None
        refresh = tokens.get('refresh_token') if isinstance(tokens, dict) else None
        if not access:
            # Fallo en renovación del token
            raise InvalidCredentialsError()
        return AuthTokenResponse(access_token=access, token_type="bearer", refresh_token=refresh)

    async def create_account(self, email: str, password: str) -> Optional[User]:
        try:
            auth_repository = SupabaseAuthRepository()
            existing_user = auth_repository.find_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            # Usar el método encapsulado en el repositorio que no expone la contraseña en logs
            created = auth_repository.create_account(email, password)
            return created
        except UserAlreadyExistsError as e:
            # Se atrapa el error de dominio y se traduce a un error HTTP
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
