from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.usecases.document_classification_use_case import (
    ClassificarDocumentosUseCase,
)
from src.domain.usecases.evaluate_eligibility_use_case import (
    EvaluateEligibilityUseCase,
)
from src.domain.usecases.build_solicitation_dashboard_use_case import (
    BuildSolicitationDashboardUseCase,
)
from src.domain.usecases.extract_data_use_case import ExtrairDadosUseCase
from src.domain.usecases.get_solicitacao_by_id_use_case import (
    GetSolicitacaoByIdUseCase,
)
from src.domain.repositories.document_repository import IDocumentRepository
from src.infra.config.settings import get_aws_settings
from src.infra.database.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from src.infra.database.repositories.document_repository import DocumentRepository
from src.infra.database.repositories.eligibility_repository import EligibilityRepository
from src.infra.database.repositories.solicitation_repository import (
    SolicitationRepository,
)
from src.infra.external.gateway.gemini_ia_gateway import GeminiIAGateway
from src.infra.external.gateway.s3_object_storage_gateway import S3ObjectStorageGateway
from src.infra.external.prompts.loader import (
    load_extraction_descriptors,
    load_validator_rules,
)

_descriptor_map = load_extraction_descriptors()

# Map categorias do classificador -> chaves de descritores disponíveis no extrator
_EXTRACTION_SYNONYMS = {
    "TERMO_DE_REPRESENTACAO": "TERMO_REPRESENTACAO",
    "PROCURACAO": "TERMO_REPRESENTACAO",
    "GPS_E_COMPROVANTE": "GPS",
    "CERTIFICADO_DE_REGULARIDADE": "RGP",
    "DECLARACAO_DE_RESIDENCIA": "COMPROVANTE_RESIDENCIA",
    "CIN": "DOCUMENTO_IDENTIDADE_RG",
    "CPF": "DOCUMENTO_IDENTIDADE",
}


def get_storage_gateway() -> S3ObjectStorageGateway:
    aws_settings = get_aws_settings()

    return S3ObjectStorageGateway(
        region=aws_settings.region, bucket=aws_settings.bucket
    )


def create_classificar_documentos_usecase(
    session: Session,
) -> ClassificarDocumentosUseCase:
    gateway = GeminiIAGateway()
    storage = get_storage_gateway()
    document_repository = DocumentRepository(session)
    solicitation_repository = SolicitationRepository(session)
    return ClassificarDocumentosUseCase(
        classificador_gateway=gateway,
        storage_gateway=storage,
        document_repository=document_repository,
        solicitation_repository=solicitation_repository,
    )


def _descriptor_resolver(classification: str) -> Optional[str]:
    key = (classification or "").upper()
    mapped = _EXTRACTION_SYNONYMS.get(key, key)
    return _descriptor_map.get(mapped)


def create_extrair_dados_use_case(session: Session) -> ExtrairDadosUseCase:
    document_repository = DocumentRepository(session)
    extraction_repository = DocumentExtractionRepository(session)
    storage_gateway = get_storage_gateway()
    extraction_gateway = GeminiIAGateway()
    return ExtrairDadosUseCase(
        document_repository=document_repository,
        extraction_repository=extraction_repository,
        storage_gateway=storage_gateway,
        extraction_gateway=extraction_gateway,
        descriptor_resolver=_descriptor_resolver,
    )


def create_avaliar_elegibilidade_use_case(
    session: Session,
) -> EvaluateEligibilityUseCase:
    solicitation_repository = SolicitationRepository(session)
    document_repository: IDocumentRepository = DocumentRepository(session)
    extraction_repository = DocumentExtractionRepository(session)
    eligibility_repository = EligibilityRepository(session)
    validator_gateway = GeminiIAGateway()
    rules_provider = load_validator_rules
    return EvaluateEligibilityUseCase(
        solicitation_repository=solicitation_repository,
        document_repository=document_repository,
        extraction_repository=extraction_repository,
        eligibility_repository=eligibility_repository,
        validator_gateway=validator_gateway,
        rules_provider=rules_provider,
    )


def create_solicitation_dashboard_use_case(
    session: Session,
) -> BuildSolicitationDashboardUseCase:
    repository = SolicitationRepository(session)
    return BuildSolicitationDashboardUseCase(repository)


def create_get_solicitacao_by_id_use_case(
    session: Session,
) -> GetSolicitacaoByIdUseCase:
    solicitation_repository = SolicitationRepository(session)
    document_repository = DocumentRepository(session)
    eligibility_repository = EligibilityRepository(session)
    return GetSolicitacaoByIdUseCase(
        solicitation_repository=solicitation_repository,
        document_repository=document_repository,
        eligibility_repository=eligibility_repository,
    )
