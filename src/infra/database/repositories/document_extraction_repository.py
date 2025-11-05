from __future__ import annotations

from typing import Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
    IDocumentExtractionRepository,
)
from src.infra.database.models import DocumentExtractionModel


class DocumentExtractionRepository(IDocumentExtractionRepository):
    """SQLAlchemy implementation of the document extraction repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _model_to_record(
        self, model: DocumentExtractionModel
    ) -> DocumentExtractionRecord:
        return DocumentExtractionRecord(
            document_id=str(model.documento_id),
            document_type=model.document_type,
            payload=model.extracted_payload,
        )

    def upsert_extraction(
        self,
        document_id: str,
        document_type: str,
        payload: Dict[str, object],
    ) -> DocumentExtractionRecord:
        existing = self._session.execute(
            select(DocumentExtractionModel).where(
                DocumentExtractionModel.documento_id == UUID(document_id)
            )
        ).scalar_one_or_none()

        if existing:
            existing.document_type = document_type
            existing.extracted_payload = payload
            self._session.add(existing)
            self._session.flush()
            return self._model_to_record(existing)

        extraction = DocumentExtractionModel(
            documento_id=UUID(document_id),
            document_type=document_type,
            extracted_payload=payload,
        )
        self._session.add(extraction)
        self._session.flush()
        return self._model_to_record(extraction)

    def get_extraction(self, document_id: str) -> Optional[DocumentExtractionRecord]:
        existing = self._session.execute(
            select(DocumentExtractionModel).where(
                DocumentExtractionModel.documento_id == UUID(document_id)
            )
        ).scalar_one_or_none()
        if existing is None:
            return None
        return self._model_to_record(existing)
