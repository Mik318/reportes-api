from fastapi import APIRouter, Depends
from ...api.dependencies import jwt_scheme
from ....domain.models import ReportRequest, ReportResponse, User
from ....application.services import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
report_service = ReportService()

@router.post("/", response_model=ReportResponse)
async def crear_reporte(data: ReportRequest, user: User = Depends(jwt_scheme)):
    return await report_service.create_report(data)

