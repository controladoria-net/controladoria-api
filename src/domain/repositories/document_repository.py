from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from src.domain.entities.document import DocumentMetadata


class IDocumentRepository(ABC):
    """Repository contract for document metadata."""

    @abstractmethod
    def create_document(self, metadata: Dict[str, object]) -> DocumentMetadata:
        """Persist document metadata and return the stored record."""

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Fetch a document by identifier."""

    @abstractmethod
    def update_classification(
        self,
        document_id: str,
        classification: str,
    ) -> None:
        """Update classification info for a document."""

    @abstractmethod
    def list_by_solicitation(self, solicitation_id: str) -> List[DocumentMetadata]:
        """Return all documents belonging to a solicitation."""
