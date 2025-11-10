from abc import ABC, abstractmethod
from typing import List

from src.domain.entities.document import (
    ClassificationDocument,
    DocumentClassification,
    DocumentMetadata,
)
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
)
from src.domain.repositories.solicitation_repository import SolicitationRecord


class IAGateway(ABC):
    @abstractmethod
    def classify(self, document: ClassificationDocument) -> DocumentClassification:
        pass

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
        pass

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
