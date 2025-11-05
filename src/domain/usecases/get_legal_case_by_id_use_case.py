from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Tuple
import time

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import (
    ExternalRateLimitError,
    InvalidInputError,
    LegalCaseNotFoundError,
    LegalCasePersistenceError,
)
from src.domain.entities.case import LegalCase, Movement
from src.domain.repositories.legal_case_repository import (
    ILegalCaseRepository,
    PersistedLegalCase,
)
from src.domain.usecases.find_legal_case_use_case import FindLegalCaseUseCase
from src.domain.core import metrics


class GetLegalCaseByIdUseCase:
    """Retrieve a legal case from persistence or external provider."""

    def __init__(
        self,
        repository: ILegalCaseRepository,
        find_use_case: FindLegalCaseUseCase,
        max_requests_per_minute: int = 60,
    ) -> None:
        self._repository = repository
        self._find_use_case = find_use_case
        self._min_interval = 60.0 / max(1, max_requests_per_minute)
        self._last_request_ts: float = 0.0

    @staticmethod
    def _validate_case_number(case_number: str) -> Either[InvalidInputError, str]:
        normalized = case_number.strip()
        if not normalized.isdigit() or len(normalized) != 20:
            return Left(
                InvalidInputError("Identificador do processo deve conter 20 dígitos.")
            )
        return Right(normalized)

    def execute(self, case_number: str) -> Either[Exception, PersistedLegalCase]:
        validation = self._validate_case_number(case_number)
        if validation.is_left():
            return Left(validation.get_left())
        normalized = validation.get_right()

        existing = self._repository.get_by_number(normalized)
        if existing:
            return Right(existing)

        domain_case = self._find_use_case.execute(normalized)
        if domain_case is None:
            return Left(LegalCaseNotFoundError(normalized))

        movements = domain_case.movement_history or []
        try:
            persisted = self._repository.insert_case_with_movements(
                case_number=normalized,
                case=domain_case,
                movements=movements,
            )
            return Right(persisted)
        except LegalCasePersistenceError as error:
            return Left(error)
        except ExternalRateLimitError as error:
            return Left(error)
        except Exception as exc:  # pylint: disable=broad-except
            return Left(LegalCasePersistenceError(str(exc)))


class UpdateStaleLegalCasesUseCase:
    """Synchronize stale legal cases with the external provider."""

    def __init__(
        self,
        repository: ILegalCaseRepository,
        find_use_case: FindLegalCaseUseCase,
        max_requests_per_minute: int = 60,
    ) -> None:
        self._repository = repository
        self._find_use_case = find_use_case
        self._min_interval = 60.0 / max(1, max_requests_per_minute)
        self._last_request_ts: float = 0.0

    @staticmethod
    def _movement_signature(movement: Movement) -> Tuple[float, str]:
        return (movement.date.timestamp(), movement.description)

    def execute(
        self,
        batch_size: int,
        stale_after_days: int = 3,
    ) -> Either[Exception, dict]:
        stale_before = datetime.now(timezone.utc) - timedelta(days=stale_after_days)
        cases = self._repository.list_stale_cases(
            limit=batch_size, stale_before=stale_before
        )

        updated = 0
        skipped = 0
        new_movements_count = 0
        field_changes_count = 0
        errors: List[str] = []

        for case in cases:
            self._respect_rate_limit()
            clean_number = "".join(
                filter(str.isdigit, case.case.case_number or case.numero_processo)
            )
            domain_case = self._find_use_case.execute(clean_number)
            if domain_case is None:
                skipped += 1
                continue

            existing_signatures = {
                self._movement_signature(movement)
                for movement in (case.case.movement_history or [])
            }
            incoming_movements = domain_case.movement_history or []
            new_movements = [
                movement
                for movement in incoming_movements
                if self._movement_signature(movement) not in existing_signatures
            ]
            field_changes_count += self._count_field_changes(case.case, domain_case)

            try:
                self._repository.apply_case_updates(case, domain_case, new_movements)
                updated += 1
                new_movements_count += len(new_movements)
            except Exception as exc:  # pylint: disable=broad-except
                errors.append(str(exc))

        summary = {
            "total_candidates": len(cases),
            "updated": updated,
            "skipped": skipped,
            "new_movements": new_movements_count,
            "field_changes": field_changes_count,
            "errors": errors,
        }
        metrics.increment("legal_cases_checked", len(cases))
        metrics.increment("legal_cases_updated", updated)
        metrics.increment("legal_case_new_movements", new_movements_count)
        metrics.increment("legal_case_update_errors", len(errors))
        return Right(summary)

    def _respect_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_ts
        if self._last_request_ts and elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_ts = time.monotonic()

    @staticmethod
    def _count_field_changes(existing: LegalCase, updated: LegalCase) -> int:
        fields = [
            "court",
            "judging_body",
            "procedural_class",
            "subject",
            "status",
            "filing_date",
            "latest_update",
        ]
        return sum(
            1
            for field in fields
            if getattr(existing, field, None) != getattr(updated, field, None)
        )
