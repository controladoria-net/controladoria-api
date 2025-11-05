from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.usecases.build_process_dashboard_use_case import (
    BuildProcessDashboardUseCase,
)
from src.domain.usecases.find_legal_case_use_case import FindLegalCaseUseCase
from src.domain.usecases.get_legal_case_by_id_use_case import (
    GetLegalCaseByIdUseCase,
    UpdateStaleLegalCasesUseCase,
)
from src.infra.config.settings import get_scheduler_settings
from src.infra.database.repositories.legal_case_repository import LegalCaseRepository
from src.infra.external.gateway.datajud_gateway import DataJudGateway


def create_find_legal_case_use_case() -> FindLegalCaseUseCase:
    return FindLegalCaseUseCase(gateway=DataJudGateway())


def create_get_legal_case_by_id_use_case(session: Session) -> GetLegalCaseByIdUseCase:
    repository = LegalCaseRepository(session)
    find_use_case = create_find_legal_case_use_case()
    rpm = get_scheduler_settings().external_rpm
    return GetLegalCaseByIdUseCase(
        repository=repository, find_use_case=find_use_case, max_requests_per_minute=rpm
    )


def create_update_stale_cases_use_case(
    session: Session,
) -> UpdateStaleLegalCasesUseCase:
    repository = LegalCaseRepository(session)
    find_use_case = create_find_legal_case_use_case()
    rpm = get_scheduler_settings().external_rpm
    return UpdateStaleLegalCasesUseCase(
        repository=repository, find_use_case=find_use_case, max_requests_per_minute=rpm
    )


def create_process_dashboard_use_case(session: Session) -> BuildProcessDashboardUseCase:
    repository = LegalCaseRepository(session)
    return BuildProcessDashboardUseCase(repository)
