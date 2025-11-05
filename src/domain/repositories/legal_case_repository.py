from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from src.domain.entities.case import LegalCase, Movement


class PersistedLegalCase:
    """Represents a legal case stored in the database with metadata."""

    def __init__(
        self,
        case: LegalCase,
        case_id: str,
        numero_processo: str,
        last_synced_at: Optional[datetime],
        prioridade: str,
        status: Optional[str],
    ) -> None:
        self.case = case
        self.case_id = case_id
        self.numero_processo = numero_processo
        self.last_synced_at = last_synced_at
        self.prioridade = prioridade
        self.status = status


class ProcessDashboardFilters:
    """Filters applied when aggregating process dashboard."""

    def __init__(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        tribunal: Optional[List[str]] = None,
        sort_field: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> None:
        self.date_from = date_from
        self.date_to = date_to
        self.status = status
        self.priority = priority
        self.tribunal = tribunal
        self.sort_field = sort_field
        self.sort_direction = sort_direction


class ProcessDashboardAggregation:
    """Aggregation result for the process dashboard."""

    def __init__(self, data: Dict[str, object]) -> None:
        self.data = data


class ILegalCaseRepository(ABC):
    """Repository contract for legal case persistence."""

    @abstractmethod
    def get_by_number(self, numero_processo: str) -> Optional[PersistedLegalCase]:
        """Return a persisted legal case if it exists."""

    @abstractmethod
    def insert_case_with_movements(
        self,
        case_number: str,
        case: LegalCase,
        movements: List[Movement],
    ) -> PersistedLegalCase:
        """Persist a new legal case and its movements."""

    @abstractmethod
    def list_stale_cases(
        self,
        limit: int,
        stale_before: datetime,
    ) -> List[PersistedLegalCase]:
        """Return a list of persisted cases that require synchronization."""

    @abstractmethod
    def apply_case_updates(
        self,
        persisted: PersistedLegalCase,
        updated_case: LegalCase,
        new_movements: List[Movement],
    ) -> PersistedLegalCase:
        """Apply case field updates and append new movements."""

    @abstractmethod
    def aggregate_dashboard(
        self, filters: ProcessDashboardFilters
    ) -> ProcessDashboardAggregation:
        """Return aggregated information for the dashboard."""
