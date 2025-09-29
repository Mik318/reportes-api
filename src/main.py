import yaml
from fastapi import FastAPI
from fastapi.responses import Response

from .infrastructure.api.routers import reports, auth

app = FastAPI(title="API Reportes IA")
app.include_router(reports.router)
app.include_router(auth.router)

@app.get("/openapi.yaml", tags=["Documentación"])
def get_openapi_yaml():
    """Descargar OpenAPI en YAML"""
    openapi_dict = app.openapi()
    yaml_str = yaml.safe_dump(openapi_dict, sort_keys=False, allow_unicode=True)
    headers = {"Content-Disposition": 'attachment; filename="openapi.yaml"'}
    return Response(content=yaml_str, media_type="application/x-yaml", headers=headers)