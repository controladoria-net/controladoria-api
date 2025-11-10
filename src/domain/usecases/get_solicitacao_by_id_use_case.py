from __future__ import annotations

import re
from typing import Optional

from src.domain.core import metrics
from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import InvalidInputError, SolicitationNotFoundError
from src.domain.entities.solicitation import (
    SolicitationDetails,
    SolicitationDocument,
)
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.repositories.eligibility_repository import (
    IEligibilityRepository,
)
from src.domain.repositories.solicitation_repository import (
    ISolicitationRepository,
    SolicitationRecord,
)

_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


class GetSolicitacaoByIdUseCase:
    """Retrieve a solicitation along with its documents."""

    def __init__(
        self,
        solicitation_repository: ISolicitationRepository,
        document_repository: IDocumentRepository,
        eligibility_repository: Optional[IEligibilityRepository] = None,
    ) -> None:
        self._solicitation_repository = solicitation_repository
        self._document_repository = document_repository
        self._eligibility_repository = eligibility_repository

    def execute(self, solicitation_id: str) -> Either[Exception, SolicitationDetails]:
        metrics.increment("solicitation_view_requests")
        identifier = (solicitation_id or "").strip()
        if not self._is_valid_uuid(identifier):
            metrics.increment("solicitation_view_errors")
            return Left(
                InvalidInputError(
                    "Identificador de solicitação inválido. Utilize um UUID válido."
                )
            )

        try:
            record = self._solicitation_repository.get_by_id(identifier)
        except SolicitationNotFoundError as exc:
            metrics.increment("solicitation_view_errors")
            return Left(exc)
        documents = self._document_repository.list_by_solicitation(identifier)

        analysis_payload = self._build_analysis_payload(record, identifier)
        lawyer_notes = self._extract_lawyer_notes(analysis_payload)
        details = SolicitationDetails(
            id=record.solicitation_id,
            pescador=record.fisher_data or None,
            status=record.status,
            priority=record.priority,
            created_at=record.created_at,
            updated_at=record.updated_at,
            analysis=analysis_payload,
            lawyer_notes=lawyer_notes,
            documents=[self._map_document(doc) for doc in documents],
        )
        metrics.increment("solicitation_view_success")
        return Right(details)

    def _build_analysis_payload(
        self, record: SolicitationRecord, solicitation_id: str
    ) -> Optional[dict]:
        analysis = dict(record.analysis) if record.analysis else None
        if not self._eligibility_repository:
            return analysis

        eligibility = self._eligibility_repository.get_by_solicitation(solicitation_id)
        if not eligibility:
            return analysis

        payload = analysis.copy() if analysis else {}
        payload.setdefault(
            "eligibility",
            {
                "status": eligibility.status,
                "score_text": eligibility.score_text,
                "pending_items": eligibility.pending_items,
            },
        )
        return payload

    @staticmethod
    def _extract_lawyer_notes(analysis: Optional[dict]) -> Optional[str]:
        if not analysis:
            return None
        raw = analysis.get("lawyerNotes")
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        return str(raw)

    @staticmethod
    def _map_document(metadata: DocumentMetadata) -> SolicitationDocument:
        return SolicitationDocument(
            id=metadata.document_id,
            file_name=metadata.file_name,
            mimetype=metadata.mimetype,
            classification=metadata.classification,
            confidence=metadata.confidence,
            uploaded_at=metadata.uploaded_at,
        )

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        return bool(_UUID_PATTERN.match(value))
