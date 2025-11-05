from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.usecases.classificar_documentos_use_case import (
    ClassificarDocumentosUseCase,
)
from src.infra.config.settings import get_aws_settings
from src.infra.database.repositories.document_repository import DocumentRepository
from src.infra.database.repositories.solicitation_repository import (
    SolicitationRepository,
)
from src.infra.external.gateway.gemini_classificador_gateway import (
    GeminiClassificadorGateway,
)
from src.infra.external.gateway.s3_object_storage_gateway import S3ObjectStorageGateway


def get_classificador_gateway() -> GeminiClassificadorGateway:
    gw = GeminiClassificadorGateway()
    gw.configurar()
    return gw


def get_storage_gateway() -> S3ObjectStorageGateway:
    aws_settings = get_aws_settings()

    return S3ObjectStorageGateway(
        region=aws_settings.region, bucket=aws_settings.bucket
    )


def create_classificar_documentos_usecase(
    session: Session,
) -> ClassificarDocumentosUseCase:
    gateway = get_classificador_gateway()
    storage = get_storage_gateway()
    document_repository = DocumentRepository(session)
    solicitation_repository = SolicitationRepository(session)
    return ClassificarDocumentosUseCase(
        classificador_gateway=gateway,
        storage_gateway=storage,
        document_repository=document_repository,
        solicitation_repository=solicitation_repository,
    )
