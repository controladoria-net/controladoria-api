from typing import Union

import requests
from requests import Response

from src.domain.core.either import Left, Right
from src.domain.core.errors import InvalidCredentialsError, TokenRefreshError
from src.domain.entities.auth import AuthTokenEntity
from src.domain.gateway.auth_gateway import (
    IAuthGateway,
    LoginResult,
    LogoutResult,
    RefreshResult,
)
from src.infra.external.keycloak.keycloak_config import KeycloakConfig
from src.domain.core.logger import get_logger

logger = get_logger(__name__)


class KeycloakAuthGateway(IAuthGateway):
    def __init__(self, config: KeycloakConfig) -> None:
        self.config = config

    def login(self, username: str, password: str) -> LoginResult:
        payload = {
            "grant_type": "password",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "username": username,
            "password": password,
            "scope": "openid profile email",
        }

        try:
            response = requests.post(self.config.token_url, data=payload)
            return self._handle_token_response(response, InvalidCredentialsError())
        except requests.RequestException as exc:
            logger.error("Erro de conexão com Keycloak (login): %s", exc)
            return Left(InvalidCredentialsError())

    def refresh_token(self, refresh_token: str) -> RefreshResult:
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        try:
            response = requests.post(self.config.token_url, data=payload)
            return self._handle_token_response(response, TokenRefreshError())
        except requests.RequestException as exc:
            logger.error("Erro de conexão com Keycloak (refresh): %s", exc)
            return Left(TokenRefreshError())

    def logout(self, refresh_token: str) -> LogoutResult:
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        try:
            response = requests.post(self.config.logout_url, data=payload)

            if response.status_code == 204:
                return Right(None)

            logger.warning(
                "Falha no logout (Keycloak): %s %s",
                response.status_code,
                response.text,
            )
            # Logout failure does not block the flow, so return success with logging
            return Right(None)
        except requests.RequestException as exc:
            logger.error("Erro de conexão com Keycloak (logout): %s", exc)
            return Right(None)

    def _handle_token_response(
        self,
        response: Response,
        error: Union[InvalidCredentialsError, TokenRefreshError],
    ) -> Union[LoginResult, RefreshResult]:
        if response.status_code == 200:
            data = response.json()
            entity = AuthTokenEntity(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_in=data["expires_in"],
                refresh_expires_in=data["refresh_expires_in"],
                token_type=data["token_type"],
            )
            return Right(entity)

        logger.warning(
            "Falha na operação de token (Keycloak): %s %s",
            response.status_code,
            response.text,
        )
        return Left(error)
