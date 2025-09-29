from contextlib import asynccontextmanager
from fastapi import FastAPI

from .infrastructure.api.repositories.supabase_auth_repository import SupabaseAuthRepository
from .infrastructure.api.routers import reports, auth
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    auth_repo = SupabaseAuthRepository()
    access_token = auth_repo.sign_in_with_password(
        settings.test_email,
        settings.test_password
    )
    print(f"Token de acceso: {access_token}")
    yield
    # Shutdown (si necesitas cleanup)

app = FastAPI(title="API Reportes IA", lifespan=lifespan)

# Incluir routers
app.include_router(reports.router)

app.include_router(auth.router)
