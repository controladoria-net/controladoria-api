from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import io
from typing import List, Sequence, Tuple
from uuid import uuid4

from src.domain.core.either import Either, Left, Right
from src.domain.core.logger import get_logger
from src.domain.core.errors import (
    ClassificationError,
    InvalidInputError,
    StorageError,
    UploadError,
)
from src.domain.entities.document import ClassificationDocument, DocumentClassification
from src.domain.gateway.ia_gateway import IAGateway
from src.domain.gateway.object_storage_gateway import IObjectStorageGateway
from src.domain.repositories.document_repository import (
    DocumentMetadata,
    IDocumentRepository,
)
from src.domain.repositories.solicitation_repository import ISolicitationRepository
from src.domain.core import metrics


MAX_DOCUMENTS_PER_REQUEST = 15
ALLOWED_CONTENT_TYPES: Sequence[str] = (
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
)


@dataclass
class ClassificationResultDocument:
    document_id: str
    classification: DocumentClassification


@dataclass
class ClassificationResult:
    solicitation_id: str
    documents: List[ClassificationResultDocument]


class DocumentClassificationUseCase:
    """Classifies documents, storing them in S3 and persisting metadata."""

    def __init__(
        self,
        ia_gateway: IAGateway,
        storage_gateway: IObjectStorageGateway,
        document_repository: IDocumentRepository,
        solicitation_repository: ISolicitationRepository,
        *,
        max_workers: int | None = None,
    ) -> None:
        self._ia_gateway = ia_gateway
        self._storage_gateway = storage_gateway
        self._document_repository = document_repository
        self._solicitation_repository = solicitation_repository
        self._logger = get_logger(__name__)
        self._max_workers = max(1, max_workers or 1)

    def execute(
        self,
        user_id: str,
        documents: List[ClassificationDocument],
    ) -> Either[Exception, ClassificationResult]:
        if not documents:
            return Left(InvalidInputError("Nenhum documento fornecido."))
        if len(documents) > MAX_DOCUMENTS_PER_REQUEST:
            metrics.increment("document_upload_errors")
            return Left(
                InvalidInputError("Quantidade máxima de 15 documentos excedida.")
            )

        created = self._solicitation_repository.create()
        solicitation_id = created.solicitation_id

        try:
            self._solicitation_repository.ensure_exists(solicitation_id)
        except Exception as exc:
            return Left(exc)

        result = ClassificationResult(
            solicitation_id=solicitation_id,
            documents=[],
        )

        prepared_documents: List[Tuple[DocumentMetadata, ClassificationDocument]] = []

        for document in documents:
            if document.mimetype not in ALLOWED_CONTENT_TYPES:
                metrics.increment("document_upload_errors")
                return Left(
                    InvalidInputError(f"Formato não suportado para '{document.name}'.")
                )

            upload_key = self._build_storage_key(solicitation_id, document.name)
            metadata: DocumentMetadata = None
            try:
                upload_stream = io.BytesIO(document.data)
                self._storage_gateway.upload(
                    upload_key, upload_stream, document.mimetype
                )
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_upload_errors")
                return Left(UploadError(str(exc)))

            try:
                # TODO: verificar se o documento já foi classificado antes
                metadata = self._document_repository.create_document(
                    {
                        "solicitacao_id": solicitation_id,
                        "nome_arquivo": document.name,
                        "mimetype": document.mimetype,
                        "s3_key": upload_key,
                        "uploaded_by": user_id,
                    }
                )
            except Exception as exc:
                metrics.increment("document_storage_errors")
                return Left(StorageError(str(exc)))

            prepared_documents.append((metadata, document))

        classified_pairs = self._classify_documents(prepared_documents)

        for metadata, classification in classified_pairs:
            result.documents.append(
                ClassificationResultDocument(
                    document_id=metadata.document_id,
                    classification=classification.value,
                )
            )

            try:
                self._document_repository.update_classification(
                    metadata.document_id,
                    classification,
                )
            except Exception:
                pass

        if not result.documents:
            metrics.increment("document_classification_errors")

            return Left(
                ClassificationError(
                    "Não foi possível classificar os documentos enviados."
                )
            )

        classified_count = len(result.documents)
        metrics.increment("documents_classified", classified_count)
        return Right(result)

    def _classify_documents(
        self,
        prepared_documents: List[Tuple[DocumentMetadata, ClassificationDocument]],
    ) -> List[Tuple[DocumentMetadata, DocumentClassification]]:
        if not prepared_documents:
            return []

        worker_count = min(self._max_workers, len(prepared_documents))
        results: List[Tuple[DocumentMetadata, DocumentClassification]] = []
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(self._ia_gateway.classify, document): (
                    metadata,
                    document,
                )
                for metadata, document in prepared_documents
            }
            for future in as_completed(future_map):
                metadata, document = future_map[future]
                try:
                    classification = future.result()
                except Exception as exc:  # pylint: disable=broad-except
                    metrics.increment("document_classification_errors")
                    self._logger.warning(
                        "Falha ao classificar '%s': %s",
                        document.name,
                        exc,
                        exc_info=True,
                    )
                    continue

                metrics.increment("classify_tasks_completed")
                results.append((metadata, classification))
        return results

    @staticmethod
    def _build_storage_key(solicitation_id: str, filename: str) -> str:
        extension = ""
        if "." in filename:
            extension = filename[filename.rfind(".") :]
        unique_id = uuid4().hex
        return f"solicitacoes/{solicitation_id}/docs/{unique_id}{extension}"
