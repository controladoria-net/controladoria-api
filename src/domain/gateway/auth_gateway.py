from abc import ABC, abstractmethod

from src.domain.core.either import Either
from src.domain.core.errors import (
    InvalidCredentialsError,
    LogoutError,
    TokenRefreshError,
)
from src.domain.entities.auth import AuthTokenEntity

LoginResult = Either[InvalidCredentialsError, AuthTokenEntity]
RefreshResult = Either[TokenRefreshError, AuthTokenEntity]
LogoutResult = Either[LogoutError, None]


class IAuthGateway(ABC):
    """Authentication gateway contract."""

    @abstractmethod
    def login(self, username: str, password: str) -> LoginResult:
        """Authenticate a user and return the associated tokens."""

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> RefreshResult:
        """Refresh authentication tokens using a refresh token."""

    @abstractmethod
    def logout(self, refresh_token: str) -> LogoutResult:
        """Invalidate a refresh token in the identity provider."""
