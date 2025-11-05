from __future__ import annotations

from abc import ABC, abstractmethod


class IDocumentExtractionGateway(ABC):
    """Gateway contract for AI based document extraction."""

    @abstractmethod
    def extract(
        self,
        *,
        document_type: str,
        document_name: str,
        mimetype: str,
        file_bytes: bytes,
        descriptor: str,
    ) -> dict:
        """Return structured data extracted from a document."""
