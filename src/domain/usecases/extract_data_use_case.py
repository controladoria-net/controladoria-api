from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

from src.domain.core.either import Either, Left, Right
from src.domain.core.errors import (
    DocumentNotFoundError,
    ExtractionError,
    InvalidInputError,
    StorageError,
    UnsupportedDocumentError,
)
from src.domain.gateway.ia_gateway import IAGateway
from src.domain.gateway.object_storage_gateway import IObjectStorageGateway
from src.domain.repositories.document_extraction_repository import (
    DocumentExtractionRecord,
    IDocumentExtractionRepository,
)
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.core import metrics
from src.domain.core.concurrency import get_lock


PromptResolver = Callable[[str], Optional[str]]


class ExtractionResult:
    """Value object bundling the extraction records."""

    def __init__(
        self, records: List[DocumentExtractionRecord], solicitation_id: Optional[str]
    ):
        self.records = records
        self.solicitation_id = solicitation_id


class ExtractDataUseCase:
    """Runs document extraction using configured AI prompts."""

    def __init__(
        self,
        document_repository: IDocumentRepository,
        extraction_repository: IDocumentExtractionRepository,
        storage_gateway: IObjectStorageGateway,
        extraction_gateway: IAGateway,
        *,
        max_workers: int | None = None,
    ) -> None:
        self._document_repository = document_repository
        self._extraction_repository = extraction_repository
        self._storage_gateway = storage_gateway
        self._extraction_gateway = extraction_gateway
        self._max_workers = max(1, max_workers or 1)

    def execute(self, document_ids: List[str]) -> Either[Exception, ExtractionResult]:
        if not document_ids:
            metrics.increment("document_extraction_errors")
            return Left(InvalidInputError("Nenhum documento informado para extração."))

        metrics.increment("document_extraction_requests", len(document_ids))

        records: List[DocumentExtractionRecord] = []
        solicitation_id: Optional[str] = None
        mixed_solicitations = False
        documents: List[DocumentMetadata] = []
        for document_id in document_ids:
            document = self._document_repository.get_document(document_id)
            if document is None:
                metrics.increment("document_extraction_errors")
                return Left(DocumentNotFoundError(document_id))

            if solicitation_id is None:
                solicitation_id = document.solicitation_id
            elif solicitation_id != document.solicitation_id:
                mixed_solicitations = True

            documents.append(document)

        extraction_payloads = self._parallel_extract(documents)
        if extraction_payloads.is_left():
            return Left(extraction_payloads.get_left())
        payload_map = extraction_payloads.get_right()

        for document in documents:
            payload = payload_map[document.document_id]
            record = self._extraction_repository.upsert_extraction(
                document_id=document.document_id,
                document_type=document.classification or "unknown",
                payload=payload,
            )
            records.append(record)

        metrics.increment("document_extractions_processed", len(records))
        if not records:
            return Left(
                UnsupportedDocumentError(
                    "Nenhum documento com tipo suportado para extração."
                )
            )
        resolved_solicitation = None if mixed_solicitations else solicitation_id
        return Right(
            ExtractionResult(records=records, solicitation_id=resolved_solicitation)
        )

    def _resolve_descriptor(self, metadata: DocumentMetadata) -> Optional[str]:
        classification = metadata.classification
        if not classification:
            return None
        return self._descriptor_resolver(classification)

    def _parallel_extract(
        self, documents: List[DocumentMetadata]
    ) -> Either[Exception, Dict[str, dict]]:
        if not documents:
            return Right({})

        payloads: Dict[str, dict] = {}
        worker_count = min(self._max_workers, len(documents))
        futures = {}
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for document in documents:
                futures[executor.submit(self._download_and_extract, document)] = (
                    document
                )

            for future in as_completed(futures):
                document = futures[future]
                try:
                    raw_payload = future.result()
                    payloads[document.document_id] = self._ensure_serializable(
                        raw_payload
                    )
                    metrics.increment("extract_tasks_completed")
                except UnsupportedDocumentError as exc:
                    metrics.increment("document_extraction_errors")
                    self._cancel_futures(futures)
                    return Left(exc)
                except StorageError as exc:
                    metrics.increment("document_extraction_errors")
                    self._cancel_futures(futures)
                    return Left(exc)
                except ExtractionError as exc:
                    metrics.increment("document_extraction_errors")
                    self._cancel_futures(futures)
                    return Left(exc)
                except Exception as exc:  # pylint: disable=broad-except
                    metrics.increment("document_extraction_errors")
                    self._cancel_futures(futures)
                    return Left(ExtractionError(str(exc)))

        return Right(payloads)

    def _download_and_extract(self, document: DocumentMetadata) -> dict:
        lock = get_lock(document.document_id)
        with lock:
            try:
                file_bytes = self._storage_gateway.download(document.s3_key)
            except Exception as exc:  # pylint: disable=broad-except
                raise StorageError(str(exc)) from exc

            try:
                return self._extraction_gateway.extract(
                    document=document,
                    file_bytes=file_bytes,
                )
            except UnsupportedDocumentError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                raise ExtractionError(str(exc)) from exc

    @staticmethod
    def _cancel_futures(futures) -> None:
        for future in futures:
            future.cancel()

    def _ensure_serializable(self, payload: Any) -> Any:
        if isinstance(payload, BaseModel):
            return self._ensure_serializable(payload.model_dump())
        if isinstance(payload, dict):
            return {
                key: self._ensure_serializable(value) for key, value in payload.items()
            }
        if isinstance(payload, list):
            return [self._ensure_serializable(item) for item in payload]
        if isinstance(payload, (datetime, date)):
            return payload.isoformat()
        return payload
