from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import InvalidInputError, SolicitationNotFoundError
from src.domain.entities.auth import AuthenticatedUserEntity
from src.domain.entities.solicitation import SolicitationDetails, SolicitationDocument
from src.infra.http.fastapi.app import create_app


class FakeUseCase:
    def __init__(
        self, result: Either[Exception, SolicitationDetails], should_raise=False
    ):
        self._result = result
        self._should_raise = should_raise

    def execute(self, solicitation_id: str) -> Either[Exception, SolicitationDetails]:
        if self._should_raise:
            raise RuntimeError("boom")
        return self._result


def build_details() -> SolicitationDetails:
    solicitation_id = str(uuid4())
    now = datetime.now(timezone.utc)
    document = SolicitationDocument(
        id=str(uuid4()),
        file_name="arquivo.pdf",
        mimetype="application/pdf",
        classification="CLASSIFICACAO",
        confidence=0.95,
        uploaded_at=now,
    )
    return SolicitationDetails(
        id=solicitation_id,
        pescador={"nome": "Maria"},
        status="pendente",
        priority="baixa",
        created_at=now,
        updated_at=now,
        analysis={"lawyerNotes": "Analisar com urgência"},
        lawyer_notes="Analisar com urgência",
        documents=[document],
    )


@pytest.fixture(name="client")
def fixture_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app()

    def override_authenticated_user() -> AuthenticatedUserEntity:
        return AuthenticatedUserEntity(
            id="user-id",
            username="test",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            roles=["admin"],
        )

    from src.infra.http.security.auth_decorator import AuthenticatedUser

    app.dependency_overrides[AuthenticatedUser] = override_authenticated_user
    return TestClient(app)


def patch_use_case(
    monkeypatch: pytest.MonkeyPatch, result: Any, should_raise: bool = False
) -> None:
    def factory(_session):
        return FakeUseCase(result, should_raise=should_raise)

    monkeypatch.setattr(
        "src.infra.http.fastapi.router.solicitacoes_router.create_get_solicitacao_by_id_use_case",
        factory,
    )


def test_get_solicitacao_returns_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    details = build_details()
    patch_use_case(monkeypatch, Right(details))

    response = client.get(f"/solicitacoes/{details.id}")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["errors"] is None
    data = payload["data"]
    assert data["id"] == details.id
    assert data["priority"] == "baixa"
    assert data["lawyerNotes"] == "Analisar com urgência"
    assert len(data["documents"]) == 1
    assert data["documents"][0]["fileName"] == "arquivo.pdf"


def test_get_solicitacao_returns_404_for_missing_resource(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    patch_use_case(
        monkeypatch,
        Left(SolicitationNotFoundError("missing-id")),
    )

    response = client.get(f"/solicitacoes/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    payload = response.json()
    assert payload["data"] is None
    assert "não foi encontrada" in payload["errors"][0]["message"].lower()


def test_get_solicitacao_returns_422_for_invalid_identifier(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    patch_use_case(
        monkeypatch,
        Left(InvalidInputError("Identificador inválido")),
    )

    response = client.get("/solicitacoes/not-a-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    payload = response.json()
    assert payload["data"] is None
    assert payload["errors"][0]["message"] == "Identificador inválido"


def test_get_solicitacao_returns_500_on_unexpected_exception(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    patch_use_case(monkeypatch, Right(build_details()), should_raise=True)

    response = client.get(f"/solicitacoes/{uuid4()}")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    payload = response.json()
    assert payload["errors"][0]["message"] == "Erro interno ao recuperar a solicitação."
