from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from src.domain.core.errors import InvalidInputError, SolicitationNotFoundError
from src.domain.entities.solicitation import SolicitationDetails
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.repositories.eligibility_repository import (
    EligibilityRecord,
    IEligibilityRepository,
)
from src.domain.repositories.solicitation_repository import (
    ISolicitationRepository,
    SolicitationDashboardAggregation,
    SolicitationDashboardFilters,
    SolicitationRecord,
)
from src.domain.usecases.get_solicitacao_by_id_use_case import (
    GetSolicitacaoByIdUseCase,
)


class FakeSolicitationRepository(ISolicitationRepository):
    def __init__(self, records: Dict[str, SolicitationRecord]) -> None:
        self._records = records

    def ensure_exists(self, solicitation_id: str) -> None:
        if solicitation_id not in self._records:
            raise SolicitationNotFoundError(solicitation_id)

    def get_by_id(self, solicitation_id: str) -> SolicitationRecord:
        try:
            return self._records[solicitation_id]
        except KeyError as exc:
            raise SolicitationNotFoundError(solicitation_id) from exc

    def update_status(self, solicitation_id: str, status: str) -> None:
        raise NotImplementedError

    def dashboard(
        self, filters: SolicitationDashboardFilters
    ) -> SolicitationDashboardAggregation:
        raise NotImplementedError

    def create(self, initial: Optional[Dict[str, object]] = None) -> SolicitationRecord:
        raise NotImplementedError


class FakeDocumentRepository(IDocumentRepository):
    def __init__(self, documents: Dict[str, List[DocumentMetadata]]) -> None:
        self._documents = documents

    def create_document(self, metadata: Dict[str, object]) -> DocumentMetadata:
        raise NotImplementedError

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        raise NotImplementedError

    def update_classification(
        self, document_id: str, classification: str, confidence: float
    ) -> None:
        raise NotImplementedError

    def list_by_solicitation(self, solicitation_id: str) -> List[DocumentMetadata]:
        return self._documents.get(solicitation_id, [])


class FakeEligibilityRepository(IEligibilityRepository):
    def __init__(self, records: Dict[str, EligibilityRecord]) -> None:
        self._records = records

    def upsert(
        self,
        solicitation_id: str,
        status: str,
        score_text: str,
        pending_items: list,
    ) -> EligibilityRecord:
        raise NotImplementedError

    def get_by_solicitation(self, solicitation_id: str) -> Optional[EligibilityRecord]:
        return self._records.get(solicitation_id)


def build_record(
    solicitation_id: str,
    analysis: Optional[Dict[str, object]] = None,
) -> SolicitationRecord:
    now = datetime.now(timezone.utc)
    return SolicitationRecord(
        solicitation_id=solicitation_id,
        status="pendente",
        priority="baixa",
        fisher_data={"nome": "Pescador"},
        municipality="Cidade",
        state="ST",
        analysis=analysis,
        created_at=now,
        updated_at=now,
    )


def build_document(solicitation_id: str) -> DocumentMetadata:
    return DocumentMetadata(
        document_id=str(uuid4()),
        solicitation_id=solicitation_id,
        s3_key="s3://bucket/object",
        mimetype="application/pdf",
        classification="TESTE",
        confidence=0.9,
        file_name="documento.pdf",
        uploaded_at=datetime.now(timezone.utc),
    )


def test_execute_returns_details_with_documents_and_analysis():
    solicitation_id = str(uuid4())
    record = build_record(
        solicitation_id,
        analysis={"lawyerNotes": "Acompanhamento necessário"},
    )
    document = build_document(solicitation_id)
    eligibility = EligibilityRecord(
        solicitation_id=solicitation_id,
        status="apto",
        score_text="80",
        pending_items=["Uma pendência"],
    )

    use_case = GetSolicitacaoByIdUseCase(
        solicitation_repository=FakeSolicitationRepository({solicitation_id: record}),
        document_repository=FakeDocumentRepository({solicitation_id: [document]}),
        eligibility_repository=FakeEligibilityRepository(
            {solicitation_id: eligibility}
        ),
    )

    result = use_case.execute(solicitation_id)

    assert result.is_right()
    details: SolicitationDetails = result.get_right()
    assert details.id == solicitation_id
    assert details.pescador == {"nome": "Pescador"}
    assert details.lawyer_notes == "Acompanhamento necessário"
    assert details.analysis is not None
    assert details.analysis["eligibility"]["status"] == "apto"
    assert len(details.documents) == 1
    doc = details.documents[0]
    assert doc.file_name == "documento.pdf"
    assert doc.classification == "TESTE"


def test_execute_returns_left_when_identifier_is_invalid():
    use_case = GetSolicitacaoByIdUseCase(
        solicitation_repository=FakeSolicitationRepository({}),
        document_repository=FakeDocumentRepository({}),
    )

    result = use_case.execute("not-a-uuid")

    assert result.is_left()
    error = result.get_left()
    assert isinstance(error, InvalidInputError)


def test_execute_returns_left_when_solicitation_is_missing():
    solicitation_id = str(uuid4())
    use_case = GetSolicitacaoByIdUseCase(
        solicitation_repository=FakeSolicitationRepository({}),
        document_repository=FakeDocumentRepository({}),
    )

    result = use_case.execute(solicitation_id)

    assert result.is_left()
    error = result.get_left()
    assert isinstance(error, SolicitationNotFoundError)
