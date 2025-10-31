from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from infra.http.dto.general_response_dto import GeneralResponseDTO
from infra.http.fastapi.router import legal_cases_router

from infra.http.fastapi.router import classificador_router
from infra.factories.classificador_factory import get_classificador_gateway


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_classificador_gateway()
    except Exception as e:
        # adicionar log de erro
        pass
    
    yield

app = FastAPI(
    lifespan=lifespan,
    title="API para gestão de tarefas de um escritório de advocacia",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=GeneralResponseDTO(
            data=None,
            errors=[
                {
                    "message": "Verifique os dados enviados na requisição.",
                    "details": exc.errors(),
                }
            ],
        ),
    )



app.add_exception_handler(
    RequestValidationError, handler=get_validation_exception_handler
)


@app.get("/", response_model=dict)
async def root():
    return {
        "message": "API para gestão de tarefas de um escritório de advocacia",
        "version": "1.0.0",
        "docs": "/docs",
    }


app.include_router(legal_cases_router.router)
app.include_router(classificador_router.router)
