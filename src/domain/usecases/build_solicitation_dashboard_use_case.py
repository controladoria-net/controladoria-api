from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import InvalidInputError
from src.domain.repositories.solicitation_repository import (
    ISolicitationRepository,
    SolicitationDashboardAggregation,
    SolicitationDashboardFilters,
)


class BuildSolicitationDashboardUseCase:
    """Aggregate solicitation data for dashboards."""

    def __init__(self, repository: ISolicitationRepository) -> None:
        self._repository = repository

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise InvalidInputError(f"Data inválida: {value}") from exc

    def execute(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        state: Optional[List[str]] = None,
        city: Optional[List[str]] = None,
    ) -> Either[Exception, SolicitationDashboardAggregation]:
        try:
            filters = SolicitationDashboardFilters(
                date_from=self._parse_date(date_from),
                date_to=self._parse_date(date_to),
                status=status,
                priority=priority,
                state=state,
                city=city,
            )
        except InvalidInputError as exc:
            return Left(exc)

        try:
            aggregation = self._repository.dashboard(filters)
        except Exception as exc:  # pylint: disable=broad-except
            return Left(InvalidInputError(str(exc)))
        return Right(aggregation)
