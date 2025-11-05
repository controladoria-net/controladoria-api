from functools import lru_cache

from fastapi import Depends

from src.domain.gateway.auth_gateway import IAuthGateway
from src.domain.usecases.login_use_case import LoginUseCase
from src.domain.usecases.logout_use_case import LogoutUseCase
from src.domain.usecases.refresh_token_use_case import RefreshTokenUseCase
from src.infra.external.keycloak.keycloak_auth_gateway import KeycloakAuthGateway
from src.infra.external.keycloak.keycloak_config import (
    KeycloakConfig,
    get_keycloak_config,
)


@lru_cache()
def get_auth_gateway() -> IAuthGateway:
    config: KeycloakConfig = get_keycloak_config()
    return KeycloakAuthGateway(config)


def create_login_use_case(
    gateway: IAuthGateway = Depends(get_auth_gateway),
) -> LoginUseCase:
    return LoginUseCase(gateway)


def create_logout_use_case(
    gateway: IAuthGateway = Depends(get_auth_gateway),
) -> LogoutUseCase:
    return LogoutUseCase(gateway)


def create_refresh_token_use_case(
    gateway: IAuthGateway = Depends(get_auth_gateway),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(gateway)
