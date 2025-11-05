from src.domain.gateway.auth_gateway import IAuthGateway, LogoutResult


class LogoutUseCase:
    def __init__(self, auth_gateway: IAuthGateway) -> None:
        self._auth_gateway = auth_gateway

    def execute(self, refresh_token: str) -> LogoutResult:
        return self._auth_gateway.logout(refresh_token)
