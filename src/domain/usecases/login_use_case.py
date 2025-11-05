from src.domain.gateway.auth_gateway import IAuthGateway, LoginResult


class LoginUseCase:
    def __init__(self, auth_gateway: IAuthGateway) -> None:
        self._auth_gateway = auth_gateway

    def execute(self, username: str, password: str) -> LoginResult:
        return self._auth_gateway.login(username, password)
