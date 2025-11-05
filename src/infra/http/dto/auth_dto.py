from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequestDTO(BaseModel):
    """DTO para requisição de login."""

    username: str
    password: str


class TokenResponseDTO(BaseModel):
    """DTO de resposta para login e refresh."""

    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str = Field(default="Bearer")


class LogoutResponseDTO(BaseModel):
    """DTO de resposta para logout."""

    message: str = Field(default="Logout realizado com sucesso.")


class UserResponseDTO(BaseModel):
    """DTO com os dados do usuário autenticado."""

    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
