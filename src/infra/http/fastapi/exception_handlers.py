from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from src.domain.core.logger import get_logger
from src.infra.http.dto.general_response_dto import GeneralResponseDTO

logger = get_logger(__name__)


async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    logger.info("HTTPException capturada: %s - %s", exc.status_code, exc.detail)
    response = GeneralResponseDTO(
        errors=[{"message": exc.detail, "code": exc.status_code}],
    )
    return JSONResponse(status_code=exc.status_code, content=response.model_dump())


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Erro de validação em %s: %s", request.url, exc.errors())
    response = GeneralResponseDTO(errors=exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:  # pylint: disable=broad-exception-caught
    logger.error(
        "Erro interno em %s: %s - %s",
        request.url,
        type(exc).__name__,
        exc,
        exc_info=True,
    )
    response = GeneralResponseDTO(
        errors=[{"message": "Ocorreu um erro interno inesperado no servidor."}],
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(),
    )
