from fastapi import APIRouter, Depends

from ...api.dependencies import jwt_scheme
from ....application.services import ReportService
from ....domain.models import ReportRequest, ReportResponse, User

router = APIRouter(prefix="/reports", tags=["reports"])
report_service = ReportService()


@router.post("/", response_model=ReportResponse)
async def crear_reporte(
    data: ReportRequest,
    user: User = Depends(jwt_scheme)
):
    # `jwt_scheme` ya valida el token (desde Authorization Bearer o cookie) y devuelve el User
    return await report_service.create_report(data)
