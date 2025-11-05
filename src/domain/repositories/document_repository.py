from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class DocumentMetadata:
    """Data class representing stored document metadata."""

    def __init__(
        self,
        document_id: str,
        solicitation_id: str,
        s3_key: str,
        mimetype: str,
        classification: Optional[str] = None,
        confidence: Optional[float] = None,
        file_name: Optional[str] = None,
        uploaded_at: Optional[datetime] = None,
    ) -> None:
        self.document_id = document_id
        self.solicitation_id = solicitation_id
        self.s3_key = s3_key
        self.mimetype = mimetype
        self.classification = classification
        self.confidence = confidence
        self.file_name = file_name
        self.uploaded_at = uploaded_at


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
        confidence: float,
    ) -> None:
        """Update classification info for a document."""

    @abstractmethod
    def list_by_solicitation(self, solicitation_id: str) -> List[DocumentMetadata]:
        """Return all documents belonging to a solicitation."""
