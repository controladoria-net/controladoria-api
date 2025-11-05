from __future__ import annotations

from typing import Callable, List, Optional

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import (
    DocumentNotFoundError,
    ExtractionError,
    InvalidInputError,
    StorageError,
    UnsupportedDocumentError,
)
from src.domain.gateway.object_storage_gateway import IObjectStorageGateway
from src.domain.gateway.document_extraction_gateway import IDocumentExtractionGateway
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
    IDocumentExtractionRepository,
)
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.core import metrics


PromptResolver = Callable[[str], Optional[str]]


class ExtractionResult:
    """Value object bundling the extraction records."""

    def __init__(
        self, records: List[DocumentExtractionRecord], solicitation_id: Optional[str]
    ):
        self.records = records
        self.solicitation_id = solicitation_id


class ExtrairDadosUseCase:
    """Runs document extraction using configured AI prompts."""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        extraction_repository: IDocumentExtractionRepository,
        storage_gateway: IObjectStorageGateway,
        extraction_gateway: IDocumentExtractionGateway,
        descriptor_resolver: PromptResolver,
    ) -> None:
        self._document_repository = document_repository
        self._extraction_repository = extraction_repository
        self._storage_gateway = storage_gateway
        self._extraction_gateway = extraction_gateway
        self._descriptor_resolver = descriptor_resolver

    def execute(self, document_ids: List[str]) -> Either[Exception, ExtractionResult]:
        if not document_ids:
            metrics.increment("document_extraction_errors")
            return Left(InvalidInputError("Nenhum documento informado para extração."))

        metrics.increment("document_extraction_requests", len(document_ids))

        records: List[DocumentExtractionRecord] = []
        solicitation_id: Optional[str] = None
        mixed_solicitations = False
        for document_id in document_ids:
            metadata = self._document_repository.get_document(document_id)
            if metadata is None:
                metrics.increment("document_extraction_errors")
                return Left(DocumentNotFoundError(document_id))

            if solicitation_id is None:
                solicitation_id = metadata.solicitation_id
            elif solicitation_id != metadata.solicitation_id:
                mixed_solicitations = True

            descriptor = self._resolve_descriptor(metadata)
            if descriptor is None:
                metrics.increment("document_extraction_errors")
                return Left(
                    UnsupportedDocumentError(metadata.classification or "desconhecido")
                )

            try:
                file_bytes = self._storage_gateway.download(metadata.s3_key)
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_extraction_errors")
                return Left(StorageError(str(exc)))

            try:
                payload = self._extraction_gateway.extract(
                    document_type=metadata.classification or "unknown",
                    document_name=metadata.file_name or metadata.document_id,
                    mimetype=metadata.mimetype,
                    file_bytes=file_bytes,
                    descriptor=descriptor,
                )
            except UnsupportedDocumentError as exc:
                metrics.increment("document_extraction_errors")
                return Left(exc)
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_extraction_errors")
                return Left(ExtractionError(str(exc)))

            record = self._extraction_repository.upsert_extraction(
                document_id=document_id,
                document_type=metadata.classification or "unknown",
                payload=payload,
            )
            records.append(record)

        metrics.increment("document_extractions_processed", len(records))
        resolved_solicitation = None if mixed_solicitations else solicitation_id
        return Right(
            ExtractionResult(records=records, solicitation_id=resolved_solicitation)
        )

    def _resolve_descriptor(self, metadata: DocumentMetadata) -> Optional[str]:
        classification = metadata.classification
        if not classification:
            return None
        return self._descriptor_resolver(classification)
