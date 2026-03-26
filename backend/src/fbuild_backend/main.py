from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

from fbuild_backend.api.routes.builds import router as builds_router
from fbuild_backend.api.routes.health import router as health_router
from fbuild_backend.api.routes.projects import router as projects_router
from fbuild_backend.config import settings
from fbuild_backend.db import init_db
from fbuild_backend.services.build_worker_loop import BuildWorkerLoop


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    stop_event = asyncio.Event()
    worker_loop = BuildWorkerLoop(poll_seconds=settings.worker_poll_seconds)
    worker_task = asyncio.create_task(worker_loop.run_until_stopped(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await worker_task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(health_router, prefix="/api")
app.include_router(builds_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
