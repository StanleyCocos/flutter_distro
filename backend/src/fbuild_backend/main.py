from fastapi import FastAPI

from fbuild_backend.api.routes.health import router as health_router
from fbuild_backend.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/api")

