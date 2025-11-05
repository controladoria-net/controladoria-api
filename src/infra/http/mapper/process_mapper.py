from datetime import datetime
from typing import Dict, List

from src.domain.entities.case import LegalCase, Movement
from src.domain.repositories.legal_case_repository import PersistedLegalCase
from src.infra.http.dto.process_dto import (
    DashboardCaseHighlight,
    DashboardCountItem,
    DashboardPeriodItem,
    LegalCaseMovementDTO,
    LegalCaseResponseDTO,
    ProcessDashboardDTO,
)


class ProcessMapper:
    """Mappings between domain/legal case data and HTTP DTOs."""

    @staticmethod
    def movement_to_dto(movement: Movement) -> LegalCaseMovementDTO:
        return LegalCaseMovementDTO(
            date=movement.date, description=movement.description
        )

    @staticmethod
    def case_to_dto(persisted: PersistedLegalCase) -> LegalCaseResponseDTO:
        domain_case: LegalCase = persisted.case
        movement_history = (
            [ProcessMapper.movement_to_dto(mov) for mov in domain_case.movement_history]
            if domain_case.movement_history
            else None
        )
        numero_processo = (
            domain_case.case_number
            if domain_case.case_number
            else persisted.numero_processo
        )
        return LegalCaseResponseDTO(
            numero_processo=numero_processo,
            tribunal=domain_case.court,
            orgao_julgador=domain_case.judging_body,
            classe_processual=domain_case.procedural_class,
            assunto=domain_case.subject,
            situacao=domain_case.status,
            data_ajuizamento=domain_case.filing_date,
            movimentacoes=len(domain_case.movement_history or []),
            ultima_movimentacao=(
                domain_case.movement_history[-1].date
                if domain_case.movement_history
                else None
            ),
            ultima_movimentacao_descricao=domain_case.latest_update,
            prioridade=persisted.prioridade,
            status=persisted.status,
            movement_history=movement_history,
        )

    @staticmethod
    def highlight_from_row(row: Dict[str, object]) -> DashboardCaseHighlight:
        return DashboardCaseHighlight(
            numero_processo=str(row.get("numero_processo")),
            tribunal=row.get("tribunal"),
            movimentacoes=int(row.get("movimentacoes", 0)),
            ultima_movimentacao=row.get("ultima_movimentacao"),
        )

    @staticmethod
    def dashboard_to_dto(data: Dict[str, object]) -> ProcessDashboardDTO:
        by_court = [
            DashboardCountItem(label=str(item["tribunal"]), value=int(item["count"]))
            for item in data.get("by_court", [])
        ]
        by_period = [
            DashboardPeriodItem(period=str(item["period"]), value=int(item["count"]))
            for item in data.get("by_period", [])
        ]
        top_by_movements = [
            ProcessMapper.highlight_from_row(item)
            for item in data.get("top_by_movements", [])
        ]
        last_updated = [
            ProcessMapper.highlight_from_row(item)
            for item in data.get("last_updated_list", [])
        ]
        return ProcessDashboardDTO(
            status_count=data.get("status_count", {}),
            by_court=by_court,
            by_period=by_period,
            period_granularity=str(data.get("period_granularity", "monthly")),
            avg_time_between_movements_days=float(
                data.get("avg_time_between_movements_days", 0.0)
            ),
            top_by_movements=top_by_movements,
            last_updated_list=last_updated,
        )
