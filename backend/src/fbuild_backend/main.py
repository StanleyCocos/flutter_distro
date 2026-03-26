from contextlib import asynccontextmanager

from fastapi import FastAPI

from fbuild_backend.api.routes.builds import router as builds_router
from fbuild_backend.api.routes.health import router as health_router
from fbuild_backend.api.routes.projects import router as projects_router
from fbuild_backend.config import settings
from fbuild_backend.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(builds_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
