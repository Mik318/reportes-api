from os import access

from ..domain.models import ReportRequest, ReportResponse, AuthTokenResponse
from ..genkit_flow import generar_reporte
from ..infrastructure.api.repositories.supabase_auth_repository import SupabaseAuthRepository


class ReportService:
    async def create_report(self, report_request: ReportRequest) -> ReportResponse:
        return await generar_reporte(report_request)

class AuthService:
    async def generate_authtoken(self, email: str, password: str) -> AuthTokenResponse:
        # Aquí iría la lógica real de autenticación
        auth_repository = SupabaseAuthRepository()
        access_token = auth_repository.sign_in_with_password(email, password)
        return AuthTokenResponse(access_token=access_token)
