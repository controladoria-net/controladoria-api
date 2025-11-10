import os
import sys
from typing import Any

import requests

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class _DummyResponse:
    def __init__(self, payload: Any | None = None) -> None:
        self._payload = payload or {"keys": []}

    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        return None

    def json(self) -> Any:
        return self._payload


def _dummy_get(*args: Any, **kwargs: Any) -> _DummyResponse:
    return _DummyResponse()


requests.get = _dummy_get

from src.domain.entities.auth import AuthenticatedUserEntity
from src.infra.http.security.auth_decorator import AuthenticatedUser


def _default_authenticated_user() -> AuthenticatedUserEntity:
    return AuthenticatedUserEntity(
        id="test-user",
        username="test-user",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        roles=["tester"],
    )


AuthenticatedUser.dependency = _default_authenticated_user  # type: ignore[attr-defined]
