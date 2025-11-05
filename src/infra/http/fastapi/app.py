from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from src.infra.http.fastapi.exception_handlers import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from src.infra.http.fastapi.router.legal_cases_router import (
    router as legal_cases_router,
)
from src.infra.http.fastapi.router.session_router import router as session_router

from infra.http.fastapi.router.classificador_router import router as classificador_router
from infra.factories.classificador_factory import get_classificador_gateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("Lifespan: Configurando o Gateway do Gemini...")
        gateway = get_classificador_gateway()
        gateway.configurar()

        app.state.gateway = gateway
        
    except ValueError as e:
        app.state.gateway = None 

    yield


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title="ControladorIA API",
        description="API para o ERP de escritório de advocacia.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
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

    fastapi_app.add_exception_handler(HTTPException, http_exception_handler)
    fastapi_app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    fastapi_app.add_exception_handler(Exception, generic_exception_handler)

    fastapi_app.include_router(session_router)
    fastapi_app.include_router(legal_cases_router)
    fastapi_app.include_router(classificador_router)

    @fastapi_app.get("/health", tags=["HealthCheck"])
    async def health_check():
        return {"status": "ok"}

    return fastapi_app


app = create_app()
