from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from src.domain.core.errors import SolicitationNotFoundError
from src.domain.repositories.solicitation_repository import (
    ISolicitationRepository,
    SolicitationDashboardAggregation,
    SolicitationDashboardFilters,
    SolicitationRecord,
)
from src.infra.database.models import SolicitationModel


class SolicitationRepository(ISolicitationRepository):
    """SQLAlchemy implementation for solicitation persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def ensure_exists(self, solicitation_id: str) -> None:
        exists_stmt = select(SolicitationModel.id).where(
            SolicitationModel.id == UUID(solicitation_id)
        )
        exists = self._session.execute(exists_stmt).scalar_one_or_none()
        if exists is None:
            raise SolicitationNotFoundError(solicitation_id)

    def _model_to_record(self, model: SolicitationModel) -> SolicitationRecord:
        return SolicitationRecord(
            solicitation_id=str(model.id),
            status=model.status,
            priority=model.prioridade,
            fisher_data=model.pescador,
            municipality=model.municipio,
            state=model.estado,
            analysis=model.analysis,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(self, solicitation_id: str) -> SolicitationRecord:
        model = self._session.get(SolicitationModel, UUID(solicitation_id))
        if model is None:
            raise SolicitationNotFoundError(solicitation_id)
        return self._model_to_record(model)

    def update_status(self, solicitation_id: str, status: str) -> None:
        model = self._session.get(SolicitationModel, UUID(solicitation_id))
        if model is None:
            raise SolicitationNotFoundError(solicitation_id)
        model.status = status
        model.updated_at = datetime.now(timezone.utc)
        self._session.add(model)
        self._session.flush()

    def dashboard(
        self, filters: SolicitationDashboardFilters
    ) -> SolicitationDashboardAggregation:
        base_query = select(
            SolicitationModel.id,
            SolicitationModel.status,
            SolicitationModel.created_at,
            SolicitationModel.updated_at,
            SolicitationModel.prioridade,
            SolicitationModel.estado,
            SolicitationModel.municipio,
        )

        conditions = []
        if filters.date_from:
            conditions.append(SolicitationModel.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(SolicitationModel.created_at <= filters.date_to)
        if filters.status:
            conditions.append(SolicitationModel.status.in_(filters.status))
        if filters.priority:
            conditions.append(SolicitationModel.prioridade.in_(filters.priority))
        if filters.state:
            conditions.append(SolicitationModel.estado.in_(filters.state))
        if filters.city:
            conditions.append(SolicitationModel.municipio.in_(filters.city))

        if conditions:
            base_query = base_query.where(*conditions)

        filtered = base_query.subquery()

        status_counts_stmt = (
            select(filtered.c.status, func.count())
            .select_from(filtered)
            .group_by(filtered.c.status)
        )
        status_counts = {
            row[0]: int(row[1]) for row in self._session.execute(status_counts_stmt)
        }

        # Aggregation by period (default monthly)
        date_trunc_expr = func.date_trunc("month", filtered.c.created_at)
        by_period_stmt = (
            select(func.to_char(date_trunc_expr, "YYYY-MM"), func.count())
            .select_from(filtered)
            .group_by(func.to_char(date_trunc_expr, "YYYY-MM"))
            .order_by(func.to_char(date_trunc_expr, "YYYY-MM"))
        )
        by_period = [
            {"period": row[0], "count": int(row[1])}
            for row in self._session.execute(by_period_stmt)
        ]

        # Average processing time (in days) for solicitations that are not pending
        processing_query = (
            select(
                func.avg(
                    func.extract("epoch", filtered.c.updated_at - filtered.c.created_at)
                )
            )
            .select_from(filtered)
            .where(filtered.c.status != "pendente")
        )
        avg_processing_seconds = self._session.execute(
            processing_query
        ).scalar_one_or_none()
        avg_processing_time_days = (
            float(avg_processing_seconds) / 86400.0 if avg_processing_seconds else 0.0
        )

        # Approval rate
        approval_counts_stmt = select(
            func.sum(case((filtered.c.status == "aprovada", 1), else_=0)),
            func.sum(
                case((filtered.c.status.in_(["aprovada", "reprovada"]), 1), else_=0)
            ),
        ).select_from(filtered)
        approved, total_closed = self._session.execute(approval_counts_stmt).one()
        approval_rate = (float(approved) / float(total_closed)) if total_closed else 0.0

        # Placeholder for most missing documents - requires business rules to determine missing docs
        missing_documents: List[Dict[str, object]] = []

        data = {
            "status_count": status_counts,
            "by_period": by_period,
            "period_granularity": "monthly",
            "avg_processing_time_days": round(avg_processing_time_days, 2),
            "approval_rate": round(approval_rate, 2),
            "most_missing_documents": missing_documents,
        }
        return SolicitationDashboardAggregation(data=data)

    def create(self, initial: Dict[str, object] | None = None) -> "SolicitationRecord":
        payload = initial or {}
        model = SolicitationModel(
            status=payload.get("status", "pendente"),
            prioridade=payload.get("prioridade", "baixa"),
            pescador=payload.get("pescador"),
            municipio=payload.get("municipio"),
            estado=payload.get("estado"),
            analysis=payload.get("analysis"),
        )
        self._session.add(model)
        self._session.flush()
        return self._model_to_record(model)
