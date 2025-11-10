from __future__ import annotations

from typing import Optional

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import InvalidInputError
from datetime import datetime

from src.domain.repositories.legal_case_repository import (
    ILegalCaseRepository,
    ProcessDashboardAggregation,
    ProcessDashboardFilters,
)


class BuildProcessDashboardUseCase:
    """Assembles dashboard data for legal cases."""

    def __init__(self, repository: ILegalCaseRepository) -> None:
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
        status: Optional[list[str]] = None,
        priority: Optional[list[str]] = None,
        tribunal: Optional[list[str]] = None,
        sort_field: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> Either[InvalidInputError, ProcessDashboardAggregation]:
        try:
            parsed_from = self._parse_date(date_from)
            parsed_to = self._parse_date(date_to)
            filters = ProcessDashboardFilters(
                date_from=parsed_from,
                date_to=parsed_to,
                status=status,
                priority=priority,
                tribunal=tribunal,
                sort_field=sort_field,
                sort_direction=sort_direction,
            )
            aggregation = self._repository.aggregate_dashboard(filters)
            return Right(aggregation)
        except Exception as exc:  # pylint: disable=broad-except
            return Left(InvalidInputError(str(exc)))
