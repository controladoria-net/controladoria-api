from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.domain.core.errors import (
    ClassificationError,
    DocumentNotFoundError,
    EligibilityComputationError,
    IncompleteDataError,
    InvalidInputError,
    SolicitationNotFoundError,
    StorageError,
    UnsupportedDocumentError,
    UploadError,
)
from src.domain.entities.auth import AuthenticatedUserEntity
from src.domain.entities.documento import DocumentoProcessar
from src.domain.usecases.avaliar_elegibilidade_use_case import (
    AvaliarElegibilidadeUseCase,
)
from src.domain.usecases.build_solicitation_dashboard_use_case import (
    BuildSolicitationDashboardUseCase,
)
from src.domain.usecases.classificar_documentos_use_case import (
    ClassificarDocumentosUseCase,
)
from src.domain.usecases.extrair_dados_use_case import ExtrairDadosUseCase
from src.infra.database.session import get_session
from src.infra.factories.classificador_factory import (
    create_classificar_documentos_usecase,
)
from src.infra.database.repositories.solicitation_repository import (
    SolicitationRepository,
)
from src.infra.factories.solicitacao_factories import (
    create_avaliar_elegibilidade_use_case,
    create_extrair_dados_use_case,
    create_solicitation_dashboard_use_case,
)
from src.infra.http.dto.general_response_dto import GeneralResponseDTO
from src.infra.http.mapper.solicitacao_mapper import SolicitacaoMapper
from src.infra.http.security.auth_decorator import AuthenticatedUser


router = APIRouter(prefix="/solicitacao", tags=["Solicitações"])


class ExtractionRequestDTO(BaseModel):
    solicitation_id: Optional[str] = None
    document_ids: List[str] = Field(..., min_length=1)


class EligibilityRequestDTO(BaseModel):
    solicitation_id: str


@router.post("/classificador/processar", response_model=GeneralResponseDTO)
async def classificar_documentos(
    files: List[UploadFile] = File(..., description="Documentos para classificação"),
    session=Depends(get_session),
    current_user: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case: ClassificarDocumentosUseCase = create_classificar_documentos_usecase(
        session
    )
    # Cria nova solicitação (status pendente/prioridade baixa por padrão)
    solicitation_repo = SolicitationRepository(session)
    created = solicitation_repo.create()
    solicitation_id = created.solicitation_id
    documentos = [
        DocumentoProcessar(
            file_object=upload.file,
            nome_arquivo_original=upload.filename,
            mimetype=upload.content_type,
        )
        for upload in files
    ]
    result = use_case.execute(solicitation_id, current_user.id, documentos)
    if result.is_left():
        error = result.get_left()
        if isinstance(error, InvalidInputError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(error, UploadError) or isinstance(error, ClassificationError):
            status_code = status.HTTP_502_BAD_GATEWAY
        elif isinstance(error, StorageError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(status_code=status_code, content=response.model_dump())

    classification_result = result.get_right()
    dto = SolicitacaoMapper.classification_response(
        solicitation_id,
        classification_result.groups,
        classification_result.documents,
    )
    return GeneralResponseDTO(data=dto.model_dump())


@router.post("/extracao", response_model=GeneralResponseDTO)
async def extrair_dados(
    payload: ExtractionRequestDTO,
    session=Depends(get_session),
    _: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case: ExtrairDadosUseCase = create_extrair_dados_use_case(session)
    result = use_case.execute(payload.document_ids)
    if result.is_left():
        error = result.get_left()
        if isinstance(error, DocumentNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, (InvalidInputError, UnsupportedDocumentError)):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(error, StorageError):
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            status_code = status.HTTP_502_BAD_GATEWAY
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(status_code=status_code, content=response.model_dump())

    extraction_result = result.get_right()
    solicitation_id = payload.solicitation_id or extraction_result.solicitation_id or ""
    dto = SolicitacaoMapper.extraction_response(
        solicitation_id, extraction_result.records
    )
    return GeneralResponseDTO(data=dto.model_dump())


@router.post("/elegibilidade", response_model=GeneralResponseDTO)
async def avaliar_elegibilidade(
    payload: EligibilityRequestDTO,
    session=Depends(get_session),
    _: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case: AvaliarElegibilidadeUseCase = create_avaliar_elegibilidade_use_case(
        session
    )
    result = use_case.execute(payload.solicitation_id)
    if result.is_left():
        error = result.get_left()
        if isinstance(error, SolicitationNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, IncompleteDataError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(error, EligibilityComputationError):
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(status_code=status_code, content=response.model_dump())

    record = result.get_right()
    dto = SolicitacaoMapper.eligibility_response(record)
    return GeneralResponseDTO(data=dto.model_dump())


@router.get("/dashboard", response_model=GeneralResponseDTO)
def dashboard_solicitacoes(
    session=Depends(get_session),
    _: AuthenticatedUserEntity = AuthenticatedUser,
    status_filter: list[str] | None = Query(default=None, alias="status"),
    priority: list[str] | None = Query(default=None),
    state: list[str] | None = Query(default=None, alias="uf"),
    city: list[str] | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    use_case: BuildSolicitationDashboardUseCase = (
        create_solicitation_dashboard_use_case(session)
    )
    result = use_case.execute(
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        priority=priority,
        state=state,
        city=city,
    )
    if result.is_left():
        error = result.get_left()
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(),
        )

    aggregation = result.get_right()
    dto = SolicitacaoMapper.dashboard_to_dto(aggregation)
    return GeneralResponseDTO(data=dto.model_dump())
