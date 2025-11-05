from fastapi import Response

from src.domain.entities.auth import AuthTokenEntity

COOKIE_SECURE = True
COOKIE_SAMESITE = "strict"


def set_auth_cookies(response: Response, token_entity: AuthTokenEntity) -> None:
    """Adiciona cookies httpOnly com os tokens de autenticação."""
    response.set_cookie(
        key="access_token",
        value=token_entity.access_token,
        max_age=token_entity.expires_in,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=token_entity.refresh_token,
        max_age=token_entity.refresh_expires_in,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/v1/session",
    )


def unset_auth_cookies(response: Response) -> None:
    """Remove cookies httpOnly de autenticação."""
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/v1/session",
    )
