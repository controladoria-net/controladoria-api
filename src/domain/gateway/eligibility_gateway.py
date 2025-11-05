from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
)
from src.domain.repositories.document_repository import DocumentMetadata
from src.domain.repositories.solicitation_repository import SolicitationRecord


class IEligibilityValidatorGateway(ABC):
    """Gateway responsible for running eligibility validation rules."""

    @abstractmethod
    def evaluate(
        self,
        *,
        solicitation: SolicitationRecord,
        documents: List[DocumentMetadata],
        extractions: List[DocumentExtractionRecord],
        rules_prompt: str,
    ) -> dict:
        """Return the evaluation result as a dictionary with status, score_texto and pendencias."""
