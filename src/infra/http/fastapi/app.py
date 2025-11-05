from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from src.infra.http.fastapi.exception_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.domain.core.logger import get_logger
from src.infra.config.settings import get_scheduler_settings
from src.infra.http.fastapi.middleware import RequestContextMiddleware
from src.infra.http.fastapi.router.legal_cases_router import (
    router as legal_cases_router,
)
from src.domain.core import metrics
from src.infra.http.fastapi.router.session_router import router as session_router
from src.infra.http.fastapi.router.solicitacao_router import (
    router as solicitacao_router,
)
from src.infra.scheduler.jobs import run_update_legal_cases_job
from src.infra.http.security.auth_decorator import AuthenticatedUser


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    scheduler_settings = get_scheduler_settings()
    scheduler = BackgroundScheduler(timezone=scheduler_settings.timezone)
    scheduler.add_job(
        run_update_legal_cases_job,
        CronTrigger(day="*/3", hour=0, minute=0),
        id="update_legal_cases_job",
        replace_existing=True,
    )

    scheduler.start()
    fastapi_app.state.scheduler = scheduler

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title="ControladorIA API",
        description="API para o ERP de escritório de advocacia.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    origins = [
        "http://localhost:3000",
        "https://www.controladoria.net.br",
        "https://controladoria.net.br",
    ]
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi_app.add_middleware(RequestContextMiddleware)

    fastapi_app.add_exception_handler(HTTPException, http_exception_handler)
    fastapi_app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    fastapi_app.add_exception_handler(Exception, generic_exception_handler)

    fastapi_app.include_router(session_router)
    fastapi_app.include_router(legal_cases_router)
    fastapi_app.include_router(solicitacao_router)

    @fastapi_app.get("/health", tags=["HealthCheck"])
    async def health_check():
        return {"status": "ok"}

    @fastapi_app.get("/metrics", tags=["Observability"])
    async def metrics_snapshot(user=AuthenticatedUser):
        return metrics.snapshot()

    return fastapi_app
