from __future__ import annotations

from collections import defaultdict
import io
from typing import Dict, List, Sequence
from uuid import uuid4

from src.domain.core.either import Either, Left, Right
from src.domain.core.logger import get_logger
from src.domain.core.errors import (
    ClassificationError,
    InvalidInputError,
    StorageError,
    UploadError,
)
from src.domain.entities.categorias import CategoriaDocumento
from src.domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from src.domain.gateway.classificador_gateway import IClassificadorGateway
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


class ClassificationResult:
    """Result bundle containing grouped classification outputs and metadata."""

    def __init__(
        self,
        groups: Dict[str, List[ResultadoClassificacao]],
        documents: Dict[str, DocumentMetadata],
    ):
        self.groups = groups
        self.documents = documents


class ClassificarDocumentosUseCase:
    """Classifies documents, storing them in S3 and persisting metadata."""

    def __init__(
        self,
        classificador_gateway: IClassificadorGateway,
        storage_gateway: IObjectStorageGateway,
        document_repository: IDocumentRepository,
        solicitation_repository: ISolicitationRepository,
    ) -> None:
        self._classificador_gateway = classificador_gateway
        self._storage_gateway = storage_gateway
        self._document_repository = document_repository
        self._solicitation_repository = solicitation_repository
        self._logger = get_logger(__name__)

    def execute(
        self,
        solicitation_id: str,
        user_id: str,
        documentos: List[DocumentoProcessar],
    ) -> Either[Exception, ClassificationResult]:
        if not documentos:
            return Left(InvalidInputError("Nenhum documento fornecido."))
        if len(documentos) > MAX_DOCUMENTS_PER_REQUEST:
            metrics.increment("document_upload_errors")
            return Left(
                InvalidInputError("Quantidade máxima de 15 documentos excedida.")
            )

        try:
            self._solicitation_repository.ensure_exists(solicitation_id)
        except Exception as exc:  # pylint: disable=broad-except
            return Left(exc)

        grouped: Dict[str, List[ResultadoClassificacao]] = defaultdict(list)
        document_map: Dict[str, DocumentMetadata] = {}

        for documento in documentos:
            if documento.mimetype not in ALLOWED_CONTENT_TYPES:
                metrics.increment("document_upload_errors")
                return Left(
                    InvalidInputError(
                        f"Formato não suportado para '{documento.nome_arquivo_original}'."
                    )
                )

            upload_key = self._build_storage_key(
                solicitation_id, documento.nome_arquivo_original
            )
            # Capture bytes once to avoid relying on the original UploadFile stream lifecycle
            try:
                documento.file_object.seek(0)
                file_bytes = documento.file_object.read()
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_upload_errors")
                return Left(UploadError(str(exc)))

            try:
                upload_stream = io.BytesIO(file_bytes)
                self._storage_gateway.upload(
                    upload_key, upload_stream, documento.mimetype
                )
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_upload_errors")
                return Left(UploadError(str(exc)))

            try:
                metadata = self._document_repository.create_document(
                    {
                        "solicitacao_id": solicitation_id,
                        "nome_arquivo": documento.nome_arquivo_original,
                        "mimetype": documento.mimetype,
                        "s3_key": upload_key,
                        "uploaded_by": user_id,
                    }
                )
                document_map[documento.nome_arquivo_original] = metadata
            except Exception as exc:  # pylint: disable=broad-except
                metrics.increment("document_storage_errors")
                return Left(StorageError(str(exc)))

            try:
                classify_stream = io.BytesIO(file_bytes)
                documento_temp = DocumentoProcessar(
                    file_object=classify_stream,
                    nome_arquivo_original=documento.nome_arquivo_original,
                    mimetype=documento.mimetype,
                )
                resultado = self._classificador_gateway.classificar(documento_temp)
            except Exception as exc:  # pylint: disable=broad-except
                resultado = ResultadoClassificacao(
                    classificacao=CategoriaDocumento.ERRO_NA_CLASSIFICACAO,
                    confianca=0.0,
                    arquivo=documento.nome_arquivo_original,
                    mimetype=documento.mimetype,
                )
                grouped[resultado.classificacao.value].append(resultado)
                metrics.increment("document_classification_errors")
                # Log root cause to help troubleshooting external IA issues
                self._logger.warning(
                    "Falha ao classificar '%s': %s",
                    documento.nome_arquivo_original,
                    exc,
                    exc_info=True,
                )
                continue

            categoria = resultado.classificacao.value
            grouped[categoria].append(resultado)

            try:
                self._document_repository.update_classification(
                    metadata.document_id,
                    categoria,
                    resultado.confianca,
                )
            except Exception:
                # Log-friendly but do not interrupt flow
                pass

        if not grouped:
            metrics.increment("document_classification_errors")
            return Left(
                ClassificationError(
                    "Não foi possível classificar os documentos enviados."
                )
            )

        classified_count = sum(len(items) for items in grouped.values())
        metrics.increment("documents_classified", classified_count)
        return Right(ClassificationResult(groups=grouped, documents=document_map))

    @staticmethod
    def _build_storage_key(solicitation_id: str, filename: str) -> str:
        extension = ""
        if "." in filename:
            extension = filename[filename.rfind(".") :]
        unique_id = uuid4().hex
        return f"solicitacoes/{solicitation_id}/docs/{unique_id}{extension}"
