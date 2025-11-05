import os
from functools import lru_cache

from dotenv import load_dotenv


class KeycloakConfig:
    def __init__(self) -> None:
        base_url = os.environ["KEYCLOAK_BASE_URL"]
        self.realm = os.environ["KEYCLOAK_REALM"]
        self.client_id = os.environ["KEYCLOAK_CLIENT_ID"]
        self.client_secret = os.environ["KEYCLOAK_CLIENT_SECRET"]

        # Realm endpoints
        self.base_realm_url = f"{base_url}realms/{self.realm}"
        self.token_url = f"{self.base_realm_url}/protocol/openid-connect/token"
        self.logout_url = f"{self.base_realm_url}/protocol/openid-connect/logout"
        self.certs_url = f"{self.base_realm_url}/protocol/openid-connect/certs"
        self.userinfo_url = f"{self.base_realm_url}/protocol/openid-connect/userinfo"

        # JWT settings
        self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", "RS256")
        self.jwt_audience = os.environ.get("JWT_AUDIENCE", self.client_id)


@lru_cache(maxsize=1)
def get_keycloak_config() -> KeycloakConfig:
    load_dotenv()
    return KeycloakConfig()
