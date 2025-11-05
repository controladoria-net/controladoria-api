from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.responses import JSONResponse

from src.domain.core.logger import get_logger
from src.domain.entities.auth import AuthenticatedUserEntity
from src.domain.usecases.login_use_case import LoginUseCase
from src.domain.usecases.logout_use_case import LogoutUseCase
from src.domain.usecases.refresh_token_use_case import RefreshTokenUseCase
from src.infra.factories.auth_factories import (
    create_login_use_case,
    create_logout_use_case,
    create_refresh_token_use_case,
)
from src.infra.http.dto.auth_dto import (
    LoginRequestDTO,
    LogoutResponseDTO,
    TokenResponseDTO,
    UserResponseDTO,
)
from src.infra.http.dto.general_response_dto import GeneralResponseDTO
from src.infra.http.mapper.auth_mapper import AuthMapper
from src.infra.http.security.auth_decorator import AuthenticatedUser
from src.infra.http.security.token_utils import set_auth_cookies, unset_auth_cookies

router = APIRouter(prefix="/session", tags=["Session"])
logger = get_logger(__name__)


@router.post(
    "/login", response_model=GeneralResponseDTO, status_code=status.HTTP_200_OK
)
async def login(
    response: Response,
    body: LoginRequestDTO,
    use_case: LoginUseCase = Depends(create_login_use_case),
):
    """Autentica um usuário e devolve os tokens."""
    try:
        result = use_case.execute(body.username, body.password)

        if result.is_left():
            error = result.get_left()
            logger.info("Falha no login via Keycloak: %s", error.message)
            error_response = GeneralResponseDTO(errors=[{"message": error.message}])
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.model_dump(),
            )

        token_entity = result.get_right()
        set_auth_cookies(response, token_entity)

        token_dto: TokenResponseDTO = AuthMapper.entity_to_token_response_dto(
            token_entity
        )
        return GeneralResponseDTO(data=token_dto)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Erro interno no endpoint /session/login: %s", exc, exc_info=True)
        error_response = GeneralResponseDTO(
            errors=[{"message": "Erro interno no servidor."}]
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.post(
    "/refresh",
    response_model=GeneralResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    use_case: RefreshTokenUseCase = Depends(create_refresh_token_use_case),
):
    """Atualiza tokens usando o refresh token presente no cookie httpOnly."""
    try:
        if not refresh_token:
            logger.info("Refresh token ausente ao tentar atualizar sessão.")
            error_response = GeneralResponseDTO(
                errors=[{"message": "Refresh token não encontrado."}]
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.model_dump(),
            )

        result = use_case.execute(refresh_token)

        if result.is_left():
            error = result.get_left()
            logger.info("Falha ao renovar token via Keycloak: %s", error.message)
            unset_auth_cookies(response)
            error_response = GeneralResponseDTO(errors=[{"message": error.message}])
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response.model_dump(),
            )

        token_entity = result.get_right()
        set_auth_cookies(response, token_entity)

        token_dto: TokenResponseDTO = AuthMapper.entity_to_token_response_dto(
            token_entity
        )
        return GeneralResponseDTO(data=token_dto)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error(
            "Erro interno no endpoint /session/refresh: %s", exc, exc_info=True
        )
        error_response = GeneralResponseDTO(
            errors=[{"message": "Erro interno no servidor."}]
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.post(
    "/logout",
    response_model=GeneralResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    use_case: LogoutUseCase = Depends(create_logout_use_case),
):
    """Realiza logout lógico e remove os cookies de autenticação."""
    try:
        if refresh_token:
            use_case.execute(refresh_token)

        unset_auth_cookies(response)

        return GeneralResponseDTO(data=LogoutResponseDTO())

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Erro interno no endpoint /session/logout: %s", exc, exc_info=True)
        unset_auth_cookies(response)
        error_response = GeneralResponseDTO(
            errors=[{"message": "Erro interno no servidor."}]
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )


@router.get(
    "/user",
    response_model=GeneralResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_current_user(
    current_user: AuthenticatedUserEntity = AuthenticatedUser,
):
    """Retorna os dados do usuário autenticado via cookie access_token."""
    try:
        logger.info("Acesso a /session/user por %s", current_user.id)
        user_dto: UserResponseDTO = AuthMapper.entity_to_user_response_dto(current_user)
        return GeneralResponseDTO(data=user_dto)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.error("Erro interno no endpoint /session/user: %s", exc, exc_info=True)
        raise
