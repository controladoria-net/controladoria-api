from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional


class SolicitationRecord:
    """Represents a solicitation persisted in the repository."""

    def __init__(
        self,
        solicitation_id: str,
        status: str,
        priority: str,
        fisher_data: Optional[Dict[str, object]],
        municipality: Optional[str],
        state: Optional[str],
        analysis: Optional[Dict[str, object]],
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.solicitation_id = solicitation_id
        self.status = status
        self.priority = priority
        self.fisher_data = fisher_data or {}
        self.municipality = municipality
        self.state = state
        self.analysis = analysis or {}
        self.created_at = created_at
        self.updated_at = updated_at


class SolicitationDashboardFilters:
    """Filters to aggregate solicitation dashboards."""

    def __init__(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[List[str]] = None,
        priority: Optional[List[str]] = None,
        state: Optional[List[str]] = None,
        city: Optional[List[str]] = None,
    ) -> None:
        self.date_from = date_from
        self.date_to = date_to
        self.status = status
        self.priority = priority
        self.state = state
        self.city = city


class SolicitationDashboardAggregation:
    """Aggregated data for the solicitation dashboard."""

    def __init__(self, data: Dict[str, object]) -> None:
        self.data = data


class ISolicitationRepository(ABC):
    """Repository contract for solicitations."""

    @abstractmethod
    def ensure_exists(self, solicitation_id: str) -> None:
        """Raise an error if the solicitation does not exist."""

    @abstractmethod
    def get_by_id(self, solicitation_id: str) -> SolicitationRecord:
        """Retrieve a solicitation by identifier or raise if missing."""

    @abstractmethod
    def update_status(self, solicitation_id: str, status: str) -> None:
        """Update the status of a solicitation."""

    @abstractmethod
    def dashboard(
        self, filters: SolicitationDashboardFilters
    ) -> SolicitationDashboardAggregation:
        """Produce aggregated data for the dashboard."""

    @abstractmethod
    def create(self, initial: Optional[Dict[str, object]] = None) -> SolicitationRecord:
        """Create a new solicitation record and return it."""
