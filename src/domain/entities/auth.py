from typing import List, Optional


class AuthTokenEntity:
    """Domain entity holding authentication tokens."""

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        refresh_expires_in: int,
        token_type: str,
    ) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.refresh_expires_in = refresh_expires_in
        self.token_type = token_type


class AuthenticatedUserEntity:
    """Domain entity extracted from the authenticated JWT payload."""

    def __init__(
        self,
        id: str,
        username: str,
        email: str,
        roles: List[str],
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> None:
        self.id = id
        self.username = username
        self.email = email
        self.roles = roles
        self.first_name = first_name
        self.last_name = last_name
