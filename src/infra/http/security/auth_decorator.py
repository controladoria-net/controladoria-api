from typing import Dict, List, Optional, Union

import backoff
import requests
from fastapi import Cookie, Depends, HTTPException, status
from jose import jwt, jwk
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
from pydantic import BaseModel, Field, ValidationError

from src.domain.core.logger import get_logger
from src.domain.entities.auth import AuthenticatedUserEntity
from src.infra.external.keycloak.keycloak_config import (
    KeycloakConfig,
    get_keycloak_config,
)

logger = get_logger(__name__)


class RealmAccess(BaseModel):
    roles: List[str] = Field(default_factory=list)


class JwtPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    jti: str
    iss: str
    aud: Union[str, List[str]]
    typ: str
    azp: str
    preferred_username: str
    email: Optional[str] = None
    email_verified: bool = False
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    realm_access: RealmAccess = Field(default_factory=RealmAccess)


class KeyCache:
    """Caches the Keycloak JWKS response and refreshes it on demand."""

    def __init__(self, config: KeycloakConfig) -> None:
        self.config = config
        self._jwks: Optional[Dict[str, List[Dict[str, str]]]] = None
        self.fetch_public_keys()

    @backoff.on_exception(
        backoff.expo, requests.RequestException, max_tries=5, max_time=300
    )
    def fetch_public_keys(self) -> None:
        response = requests.get(self.config.certs_url, timeout=5)
        response.raise_for_status()
        self._jwks = response.json()
        logger.info("Chaves públicas do Keycloak carregadas com sucesso.")

    def _ensure_keys(self) -> Dict[str, List[Dict[str, str]]]:
        if self._jwks is None:
            self.fetch_public_keys()
        return self._jwks or {"keys": []}

    def get_key(self, kid: str) -> Optional[Dict[str, str]]:
        jwks = self._ensure_keys()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        # Key not found; refresh once more
        self.fetch_public_keys()
        jwks = self._ensure_keys()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        logger.error("Chave pública com kid=%s não encontrada no JWKS.", kid)
        return None


class AuthGuard:
    """FastAPI dependency responsible for validating access tokens."""

    def __init__(self, required: bool = True) -> None:
        self.required = required
        self.config = get_keycloak_config()
        self.key_cache = KeyCache(self.config)
        self.unauthorized_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def __call__(
        self, access_token: Optional[str] = Cookie(default=None)
    ) -> Optional[AuthenticatedUserEntity]:
        if access_token is None:
            if self.required:
                logger.debug("Token de acesso ausente (Cookie).")
                raise self.unauthorized_exception
            return None

        try:
            header = jwt.get_unverified_header(access_token)
            kid = header.get("kid")
            if not kid:
                logger.warning("Token recebido sem 'kid' no header.")
                raise self.unauthorized_exception

            key_dict = self.key_cache.get_key(kid)
            if not key_dict:
                raise self.unauthorized_exception

            public_key = (
                jwk.construct(key_dict, self.config.jwt_algorithm)
                .to_pem()
                .decode("utf-8")
            )

            payload_dict = jwt.decode(
                token=access_token,
                key=public_key,
                algorithms=[self.config.jwt_algorithm],
                issuer=self.config.base_realm_url,
                options={"verify_aud": False},
            )

            aud_claim = payload_dict.get("aud")
            if isinstance(aud_claim, str):
                audience_values = [aud_claim]
            elif isinstance(aud_claim, list):
                audience_values = [str(value) for value in aud_claim]
            else:
                audience_values = []

            if not any(aud in self.config.jwt_audiences for aud in audience_values):
                logger.warning("Audience '%s' não autorizada.", aud_claim)
                raise self.unauthorized_exception

            payload = JwtPayload.model_validate(payload_dict)

            return AuthenticatedUserEntity(
                id=payload.sub,
                username=payload.preferred_username,
                email=payload.email or "",
                first_name=payload.given_name,
                last_name=payload.family_name,
                roles=payload.realm_access.roles,
            )

        except ExpiredSignatureError:
            logger.info("Token de acesso expirado.")
            raise self.unauthorized_exception
        except JWTClaimsError as exc:
            logger.warning("Falha na validação de claims do JWT: %s", exc)
            raise self.unauthorized_exception
        except (JWTError, ValidationError, Exception) as exc:
            logger.warning("Erro ao decodificar ou validar o token JWT: %s", exc)
            raise self.unauthorized_exception


AuthenticatedUser = Depends(AuthGuard(required=True))
OptionalUser = Depends(AuthGuard(required=False))
