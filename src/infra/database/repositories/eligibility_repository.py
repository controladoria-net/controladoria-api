from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.repositories.eligibility_repository import (
    EligibilityRecord,
    IEligibilityRepository,
)
from src.infra.database.models import EligibilityResultModel


class EligibilityRepository(IEligibilityRepository):
    """SQLAlchemy implementation for eligibility persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _model_to_record(self, model: EligibilityResultModel) -> EligibilityRecord:
        return EligibilityRecord(
            solicitation_id=str(model.solicitacao_id),
            status=model.status,
            score_text=model.score_texto,
            pending_items=model.pendencias or [],
        )

    def upsert(
        self,
        solicitation_id: str,
        status: str,
        score_text: str,
        pending_items: list,
    ) -> EligibilityRecord:
        stmt = select(EligibilityResultModel).where(
            EligibilityResultModel.solicitacao_id == UUID(solicitation_id)
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing:
            existing.status = status
            existing.score_texto = score_text
            existing.pendencias = pending_items
            self._session.add(existing)
            self._session.flush()
            return self._model_to_record(existing)

        record = EligibilityResultModel(
            solicitacao_id=UUID(solicitation_id),
            status=status,
            score_texto=score_text,
            pendencias=pending_items,
        )
        self._session.add(record)
        self._session.flush()
        return self._model_to_record(record)

    def get_by_solicitation(self, solicitation_id: str) -> Optional[EligibilityRecord]:
        stmt = select(EligibilityResultModel).where(
            EligibilityResultModel.solicitacao_id == UUID(solicitation_id)
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing is None:
            return None
        return self._model_to_record(existing)
