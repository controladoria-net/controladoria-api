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

        audience_env = os.environ.get("JWT_AUDIENCE")
        if audience_env is not None:
            parsed_audiences = [
                aud.strip() for aud in audience_env.split(",") if aud.strip()
            ]
            self.jwt_audiences = parsed_audiences or [self.client_id]
        else:
            # Default to the client_id and include 'account' which Keycloak commonly sets.
            self.jwt_audiences = [self.client_id, "account"]

        if self.client_id not in self.jwt_audiences:
            self.jwt_audiences.append(self.client_id)
        if "account" not in self.jwt_audiences:
            self.jwt_audiences.append("account")
        self.jwt_audiences = list(dict.fromkeys(self.jwt_audiences))
        self.jwt_audience = (
            self.jwt_audiences if len(self.jwt_audiences) > 1 else self.jwt_audiences[0]
        )


@lru_cache(maxsize=1)
def get_keycloak_config() -> KeycloakConfig:
    load_dotenv()
    return KeycloakConfig()
