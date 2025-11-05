from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional


class DocumentExtractionRecord:
    """Represents persisted extraction data."""

    def __init__(
        self,
        document_id: str,
        document_type: str,
        payload: Dict[str, object],
    ) -> None:
        self.document_id = document_id
        self.document_type = document_type
        self.payload = payload


class IDocumentExtractionRepository(ABC):
    """Repository contract for document extraction data."""

    @abstractmethod
    def upsert_extraction(
        self,
        document_id: str,
        document_type: str,
        payload: Dict[str, object],
    ) -> DocumentExtractionRecord:
        """Create or update an extraction payload."""

    @abstractmethod
    def get_extraction(self, document_id: str) -> Optional[DocumentExtractionRecord]:
        """Retrieve an extraction payload by document ID."""
