import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient  # noqa: E402

from src.domain.entities.auth import AuthenticatedUserEntity  # noqa: E402
from src.infra.http.fastapi.app import create_app  # noqa: E402
from src.infra.http.security.auth_decorator import AuthenticatedUser  # noqa: E402

pytest.importorskip("httpx")


def test_get_session_user_returns_authenticated_user_data():
    app = create_app()
    client = TestClient(app)

    def override_authenticated_user() -> AuthenticatedUserEntity:
        return AuthenticatedUserEntity(
            id="user-123",
            username="jdoe",
            email="jdoe@example.com",
            first_name="John",
            last_name="Doe",
            roles=["admin", "user"],
        )

    app.dependency_overrides[AuthenticatedUser.dependency] = override_authenticated_user

    response = client.get("/session/user")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["errors"] is None
    assert payload["data"] == {
        "id": "user-123",
        "username": "jdoe",
        "email": "jdoe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "roles": ["admin", "user"],
    }


def test_get_session_user_without_credentials_returns_unauthorized_response():
    app = create_app()
    client = TestClient(app)

    def override_authenticated_user() -> AuthenticatedUserEntity:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autorizado"
        )

    app.dependency_overrides[AuthenticatedUser.dependency] = override_authenticated_user

    response = client.get("/session/user")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    payload = response.json()
    assert payload["data"] is None
    assert payload["errors"][0]["message"] == "Não autorizado"
    assert payload["errors"][0]["code"] == status.HTTP_401_UNAUTHORIZED
