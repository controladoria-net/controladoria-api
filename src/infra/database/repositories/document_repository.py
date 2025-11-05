from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.infra.database.models import DocumentModel


class DocumentRepository(IDocumentRepository):
    """SQLAlchemy implementation of the document repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _model_to_metadata(self, model: DocumentModel) -> DocumentMetadata:
        return DocumentMetadata(
            document_id=str(model.id),
            solicitation_id=str(model.solicitacao_id),
            s3_key=model.s3_key,
            mimetype=model.mimetype,
            classification=model.classificacao,
            confidence=model.confianca,
            file_name=model.nome_arquivo,
            uploaded_at=model.uploaded_at,
        )

    def create_document(self, metadata: Dict[str, object]) -> DocumentMetadata:
        document = DocumentModel(
            solicitacao_id=metadata["solicitacao_id"],
            nome_arquivo=metadata["nome_arquivo"],
            mimetype=metadata["mimetype"],
            s3_key=metadata["s3_key"],
            uploaded_by=metadata["uploaded_by"],
            uploaded_at=metadata.get("uploaded_at", datetime.now(timezone.utc)),
            classificacao=metadata.get("classificacao"),
            confianca=metadata.get("confianca"),
            status=metadata.get("status"),
        )
        self._session.add(document)
        self._session.flush()
        return self._model_to_metadata(document)

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        stmt = select(DocumentModel).where(DocumentModel.id == UUID(document_id))
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_metadata(model)

    def update_classification(
        self,
        document_id: str,
        classification: str,
        confidence: float,
    ) -> None:
        model = self._session.get(DocumentModel, UUID(document_id))
        if model:
            model.classificacao = classification
            model.confianca = confidence
            self._session.add(model)
            self._session.flush()

    def list_by_solicitation(self, solicitation_id: str) -> List[DocumentMetadata]:
        stmt = select(DocumentModel).where(
            DocumentModel.solicitacao_id == UUID(solicitation_id)
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_metadata(model) for model in models]
