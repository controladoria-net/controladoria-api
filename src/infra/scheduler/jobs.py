from __future__ import annotations

from datetime import timedelta

from src.domain.core.logger import get_logger
from src.domain.core import metrics
from src.domain.usecases.get_legal_case_by_id_use_case import (
    UpdateStaleLegalCasesUseCase,
)
from src.infra.config.settings import get_scheduler_settings
from src.infra.database.repositories.scheduler_lock_repository import (
    SchedulerLockRepository,
)
from src.infra.database.session import session_scope
from src.infra.factories.legal_case_factories import create_update_stale_cases_use_case

logger = get_logger(__name__)


LOCK_NAME = "update_legal_cases_cron"


def run_update_legal_cases_job() -> None:
    settings = get_scheduler_settings()
    lock_ttl_seconds = int(timedelta(minutes=30).total_seconds())

    with session_scope() as session:
        lock_repository = SchedulerLockRepository(session)
        if not lock_repository.acquire(LOCK_NAME, lock_ttl_seconds):
            logger.info(
                "Job de atualização de processos já em execução em outra instância."
            )
            return

        try:
            use_case: UpdateStaleLegalCasesUseCase = create_update_stale_cases_use_case(
                session
            )
            result = use_case.execute(batch_size=settings.batch_size)
            if result.is_left():
                error = result.get_left()
                metrics.increment("scheduler_errors")
                logger.error("Job de atualização falhou: %s", error)
                return

            summary = result.get_right()
            metrics.increment("scheduler_runs")
            metrics.increment("scheduler_updated_cases", summary.get("updated", 0))
            logger.info(
                "Atualização de processos concluída: %s",
                summary,
            )
        finally:
            lock_repository.release(LOCK_NAME)
