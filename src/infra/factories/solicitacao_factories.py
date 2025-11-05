from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.domain.usecases.avaliar_elegibilidade_use_case import (
    AvaliarElegibilidadeUseCase,
)
from src.domain.usecases.build_solicitation_dashboard_use_case import (
    BuildSolicitationDashboardUseCase,
)
from src.domain.usecases.extrair_dados_use_case import ExtrairDadosUseCase
from src.domain.repositories.document_repository import IDocumentRepository
from src.infra.database.repositories.document_extraction_repository import (
    DocumentExtractionRepository,
)
from src.infra.database.repositories.document_repository import DocumentRepository
from src.infra.database.repositories.eligibility_repository import EligibilityRepository
from src.infra.database.repositories.solicitation_repository import (
    SolicitationRepository,
)
from src.infra.external.gateway.gemini_eligibility_gateway import (
    GeminiEligibilityGateway,
)
from src.infra.external.gateway.gemini_extractor_gateway import GeminiExtractionGateway
from src.infra.external.prompts.loader import (
    load_extraction_descriptors,
    load_validator_rules,
)
from src.infra.factories.classificador_factory import get_storage_gateway

_descriptor_map = load_extraction_descriptors()


def _get_extraction_gateway() -> GeminiExtractionGateway:
    return GeminiExtractionGateway()


def _get_eligibility_gateway() -> GeminiEligibilityGateway:
    return GeminiEligibilityGateway()


def _descriptor_resolver(classification: str) -> Optional[str]:
    return _descriptor_map.get((classification or "").upper())


def create_extrair_dados_use_case(session: Session) -> ExtrairDadosUseCase:
    document_repository = DocumentRepository(session)
    extraction_repository = DocumentExtractionRepository(session)
    storage_gateway = get_storage_gateway()
    extraction_gateway = _get_extraction_gateway()
    return ExtrairDadosUseCase(
        document_repository=document_repository,
        extraction_repository=extraction_repository,
        storage_gateway=storage_gateway,
        extraction_gateway=extraction_gateway,
        descriptor_resolver=_descriptor_resolver,
    )


def create_avaliar_elegibilidade_use_case(
    session: Session,
) -> AvaliarElegibilidadeUseCase:
    solicitation_repository = SolicitationRepository(session)
    document_repository: IDocumentRepository = DocumentRepository(session)
    extraction_repository = DocumentExtractionRepository(session)
    eligibility_repository = EligibilityRepository(session)
    validator_gateway = _get_eligibility_gateway()
    rules_provider = load_validator_rules
    return AvaliarElegibilidadeUseCase(
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
