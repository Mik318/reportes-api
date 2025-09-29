import yaml
from fastapi import FastAPI
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware

from .infrastructure.api.routers import reports, auth

app = FastAPI(title="API Reportes IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://mik318.github.io"],  # O lista de dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],  # O lista de métodos permitidos
    allow_headers=["*"],  # O lista de headers permitidos
)
app.include_router(reports.router)
app.include_router(auth.router)

@app.get("/openapi.yaml", tags=["Documentacion"])
def get_openapi_yaml():
    """Descargar OpenAPI en YAML"""
    openapi_dict = app.openapi()
    yaml_str = yaml.safe_dump(openapi_dict, sort_keys=False, allow_unicode=True)
    headers = {"Content-Disposition": 'attachment; filename="openapi.yaml"'}
    return Response(content=yaml_str, media_type="application/x-yaml", headers=headers)