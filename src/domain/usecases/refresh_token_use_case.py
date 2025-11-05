from src.domain.gateway.auth_gateway import IAuthGateway, RefreshResult


class RefreshTokenUseCase:
    def __init__(self, auth_gateway: IAuthGateway) -> None:
        self._auth_gateway = auth_gateway

    def execute(self, refresh_token: str) -> RefreshResult:
        return self._auth_gateway.refresh_token(refresh_token)
