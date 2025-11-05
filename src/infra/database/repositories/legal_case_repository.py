from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from src.domain.core.errors import LegalCasePersistenceError
from src.domain.entities.case import CNJNumber, LegalCase, Movement
from src.domain.repositories.legal_case_repository import (
    ILegalCaseRepository,
    PersistedLegalCase,
    ProcessDashboardAggregation,
    ProcessDashboardFilters,
)
from src.infra.database.models import LegalCaseModel, LegalCaseMovementModel


class LegalCaseRepository(ILegalCaseRepository):
    """SQLAlchemy implementation for legal case persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _model_to_persisted(self, model: LegalCaseModel) -> PersistedLegalCase:
        movements = (
            sorted(model.movements, key=lambda mv: mv.movement_date)
            if model.movements
            else []
        )
        domain_movements = [
            Movement(date=movement.movement_date, description=movement.description)
            for movement in movements
        ]
        numero_processo = model.numero_processo
        if numero_processo and numero_processo.isdigit() and len(numero_processo) == 20:
            try:
                numero_processo = CNJNumber.from_raw(numero_processo).number
            except ValueError:
                pass

        legal_case = LegalCase(
            case_number=numero_processo,
            court=model.tribunal,
            judging_body=model.orgao_julgador,
            procedural_class=model.classe_processual,
            subject=model.assunto,
            status=model.status,
            filing_date=model.data_ajuizamento,
            latest_update=model.ultima_movimentacao_descricao,
            movement_history=domain_movements or None,
        )
        return PersistedLegalCase(
            case=legal_case,
            case_id=str(model.id),
            numero_processo=model.numero_processo,
            last_synced_at=model.last_synced_at,
            prioridade=model.prioridade,
            status=model.status,
        )

    def get_by_number(self, numero_processo: str) -> Optional[PersistedLegalCase]:
        stmt = (
            select(LegalCaseModel)
            .options(selectinload(LegalCaseModel.movements))
            .where(LegalCaseModel.numero_processo == numero_processo)
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_persisted(model)

    def insert_case_with_movements(
        self,
        case_number: str,
        case: LegalCase,
        movements: List[Movement],
    ) -> PersistedLegalCase:
        try:
            legal_case_model = LegalCaseModel(
                numero_processo=case_number,
                tribunal=case.court,
                orgao_julgador=case.judging_body,
                classe_processual=case.procedural_class,
                assunto=case.subject,
                situacao=case.status,
                data_ajuizamento=case.filing_date,
                movimentacoes=len(movements),
                ultima_movimentacao=(movements[-1].date if movements else None),
                ultima_movimentacao_descricao=case.latest_update,
                status=case.status,
                last_synced_at=datetime.now(timezone.utc),
            )
            self._session.add(legal_case_model)
            self._session.flush()

            for movement in movements:
                movement_model = LegalCaseMovementModel(
                    legal_case_id=legal_case_model.id,
                    movement_date=movement.date,
                    description=movement.description,
                )
                self._session.add(movement_model)

            self._session.flush()
            return self._model_to_persisted(legal_case_model)
        except Exception as exc:  # pylint: disable=broad-except
            raise LegalCasePersistenceError(str(exc)) from exc

    def list_stale_cases(
        self,
        limit: int,
        stale_before: datetime,
    ) -> List[PersistedLegalCase]:
        stmt = (
            select(LegalCaseModel)
            .options(selectinload(LegalCaseModel.movements))
            .where(
                (LegalCaseModel.last_synced_at.is_(None))
                | (LegalCaseModel.last_synced_at < stale_before)
            )
            .limit(limit)
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._model_to_persisted(model) for model in models]

    def apply_case_updates(
        self,
        persisted: PersistedLegalCase,
        updated_case: LegalCase,
        new_movements: List[Movement],
    ) -> PersistedLegalCase:
        try:
            model = self._session.get(LegalCaseModel, persisted.case_id)
            if model is None:
                raise LegalCasePersistenceError(
                    "Processo não localizado para atualização."
                )

            model.tribunal = updated_case.court
            model.orgao_julgador = updated_case.judging_body
            model.classe_processual = updated_case.procedural_class
            model.assunto = updated_case.subject
            model.situacao = updated_case.status
            model.status = updated_case.status
            model.data_ajuizamento = updated_case.filing_date
            ordered_movements = sorted(
                updated_case.movement_history or [], key=lambda m: m.date
            )
            model.ultima_movimentacao = (
                ordered_movements[-1].date if ordered_movements else None
            )
            model.ultima_movimentacao_descricao = updated_case.latest_update
            model.movimentacoes = len(ordered_movements)
            model.last_synced_at = datetime.now(timezone.utc)

            for movement in new_movements:
                movement_model = LegalCaseMovementModel(
                    legal_case_id=model.id,
                    movement_date=movement.date,
                    description=movement.description,
                )
                self._session.add(movement_model)

            self._session.flush()
            return self._model_to_persisted(model)
        except LegalCasePersistenceError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            raise LegalCasePersistenceError(str(exc)) from exc

    def aggregate_dashboard(
        self, filters: ProcessDashboardFilters
    ) -> ProcessDashboardAggregation:
        base_query = select(
            LegalCaseModel.id,
            LegalCaseModel.numero_processo,
            LegalCaseModel.tribunal,
            LegalCaseModel.status,
            LegalCaseModel.prioridade,
            LegalCaseModel.movimentacoes,
            LegalCaseModel.data_ajuizamento,
            LegalCaseModel.ultima_movimentacao,
            LegalCaseModel.created_at,
        )

        conditions = []
        if filters.date_from:
            conditions.append(LegalCaseModel.created_at >= filters.date_from)
        if filters.date_to:
            conditions.append(LegalCaseModel.created_at <= filters.date_to)
        if filters.status:
            conditions.append(LegalCaseModel.status.in_(filters.status))
        if filters.priority:
            conditions.append(LegalCaseModel.prioridade.in_(filters.priority))
        if filters.tribunal:
            conditions.append(LegalCaseModel.tribunal.in_(filters.tribunal))

        if conditions:
            base_query = base_query.where(*conditions)

        filtered = base_query.subquery()

        status_counts_stmt = select(filtered.c.status, func.count()).group_by(
            filtered.c.status
        )
        status_count = {
            row[0] or "desconhecido": int(row[1])
            for row in self._session.execute(status_counts_stmt)
        }

        by_court_stmt = (
            select(filtered.c.tribunal, func.count())
            .group_by(filtered.c.tribunal)
            .order_by(desc(func.count()))
        )
        by_court = [
            {"tribunal": row[0] or "desconhecido", "count": int(row[1])}
            for row in self._session.execute(by_court_stmt)
        ]

        date_trunc = func.date_trunc("month", filtered.c.created_at)
        by_period_stmt = (
            select(func.to_char(date_trunc, "YYYY-MM"), func.count())
            .group_by(func.to_char(date_trunc, "YYYY-MM"))
            .order_by(func.to_char(date_trunc, "YYYY-MM"))
        )
        by_period = [
            {"period": row[0], "count": int(row[1])}
            for row in self._session.execute(by_period_stmt)
        ]

        avg_time_expr = func.avg(
            func.extract(
                "epoch",
                filtered.c.ultima_movimentacao - filtered.c.data_ajuizamento,
            )
            / func.nullif(filtered.c.movimentacoes, 0)
        )
        avg_time_seconds = (
            self._session.execute(select(avg_time_expr)).scalar_one_or_none() or 0.0
        )
        avg_time_days = float(avg_time_seconds) / 86400.0 if avg_time_seconds else 0.0

        top_by_movements_stmt = (
            select(
                filtered.c.numero_processo,
                filtered.c.tribunal,
                filtered.c.movimentacoes,
                filtered.c.ultima_movimentacao,
            )
            .order_by(desc(filtered.c.movimentacoes))
            .limit(5)
        )
        top_by_movements = [
            {
                "numero_processo": row[0],
                "tribunal": row[1],
                "movimentacoes": int(row[2] or 0),
                "ultima_movimentacao": row[3],
            }
            for row in self._session.execute(top_by_movements_stmt)
        ]

        last_updated_stmt = (
            select(
                filtered.c.numero_processo,
                filtered.c.tribunal,
                filtered.c.movimentacoes,
                filtered.c.ultima_movimentacao,
            )
            .order_by(desc(filtered.c.ultima_movimentacao))
            .limit(5)
        )
        last_updated = [
            {
                "numero_processo": row[0],
                "tribunal": row[1],
                "movimentacoes": int(row[2] or 0),
                "ultima_movimentacao": row[3],
            }
            for row in self._session.execute(last_updated_stmt)
        ]

        data = {
            "status_count": status_count,
            "by_court": by_court,
            "by_period": by_period,
            "period_granularity": "monthly",
            "avg_time_between_movements_days": round(avg_time_days, 2),
            "top_by_movements": top_by_movements,
            "last_updated_list": last_updated,
        }
        return ProcessDashboardAggregation(data=data)
