from ..domain.models import ReportRequest, ReportResponse
from ..genkit_flow import generar_reporte

class ReportService:
    async def create_report(self, report_request: ReportRequest) -> ReportResponse:
        return await generar_reporte(report_request)

