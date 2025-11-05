from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class EligibilityRecord:
    """Represents the persisted eligibility evaluation."""

    def __init__(
        self,
        solicitation_id: str,
        status: str,
        score_text: str,
        pending_items: Optional[list] = None,
    ) -> None:
        self.solicitation_id = solicitation_id
        self.status = status
        self.score_text = score_text
        self.pending_items = pending_items or []


class IEligibilityRepository(ABC):
    """Repository contract for eligibility evaluations."""

    @abstractmethod
    def upsert(
        self,
        solicitation_id: str,
        status: str,
        score_text: str,
        pending_items: list,
    ) -> EligibilityRecord:
        """Store the eligibility result."""

    @abstractmethod
    def get_by_solicitation(self, solicitation_id: str) -> Optional[EligibilityRecord]:
        """Fetch the eligibility result for a solicitation."""
