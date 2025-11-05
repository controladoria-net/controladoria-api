class DomainError(Exception):
    """Base error for the domain layer."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidCredentialsError(DomainError):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__("Credenciais inválidas. Verifique usuário e senha.")


class TokenRefreshError(DomainError):
    """Raised when refresh token flow fails."""

    def __init__(self) -> None:
        super().__init__("Não foi possível atualizar o token. Faça login novamente.")


class TokenValidationError(DomainError):
    """Raised when the access token is invalid or expired."""

    def __init__(self, message: str = "Token de acesso inválido ou expirado.") -> None:
        super().__init__(message)


class LogoutError(DomainError):
    """Raised when the logout operation cannot be completed."""

    def __init__(self, message: str = "Erro ao processar o logout.") -> None:
        super().__init__(message)
