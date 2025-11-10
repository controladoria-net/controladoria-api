from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.domain.core.errors import (
    ClassificationError,
    DocumentNotFoundError,
    DomainError,
    EligibilityComputationError,
    IncompleteDataError,
    InvalidInputError,
    SolicitationNotFoundError,
    StorageError,
    UnsupportedDocumentError,
    UploadError,
)
from src.domain.entities.auth import AuthenticatedUserEntity

from src.domain.entities.document import ClassificationDocument
from src.domain.usecases.evaluate_eligibility_use_case import (
    EvaluateEligibilityUseCase,
)
from src.domain.usecases.build_solicitation_dashboard_use_case import (
    BuildSolicitationDashboardUseCase,
)
from src.domain.usecases.document_classification_use_case import (
    ClassificarDocumentosUseCase,
)
from src.domain.usecases.extract_data_use_case import ExtrairDadosUseCase
from src.infra.database.session import get_session
from src.infra.factories.solicitation_factory import (
    create_classificar_documentos_usecase,
)
from src.infra.factories.solicitation_factory import (
    create_avaliar_elegibilidade_use_case,
    create_extrair_dados_use_case,
    create_get_solicitacao_by_id_use_case,
    create_solicitation_dashboard_use_case,
)
from src.infra.http.dto.general_response_dto import GeneralResponseDTO
from src.infra.http.mapper.solicitacao_mapper import SolicitacaoMapper
from src.infra.http.security.auth_decorator import AuthenticatedUser


router = APIRouter(prefix="/solicitacao", tags=["Solicitações"])


class ExtractionRequestDTO(BaseModel):
    solicitation_id: Optional[str] = None
    document_ids: Optional[List[str]] = Field(default=None)


class EligibilityRequestDTO(BaseModel):
    solicitation_id: str


@router.post("/classificador", response_model=GeneralResponseDTO)
async def classificar_documentos(
    files: List[UploadFile] = File(..., description="Documentos para classificação"),
    session=Depends(get_session),
    current_user: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case: ClassificarDocumentosUseCase = create_classificar_documentos_usecase(
        session
    )
    documents = [
        ClassificationDocument(
            data=await _file.read(),
            name=_file.filename,
            mimetype=_file.content_type,
        )
        for _file in files
    ]
    result = use_case.execute(current_user.id, documents)

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

    return GeneralResponseDTO(data=classification_result)


@router.post("/extracao", response_model=GeneralResponseDTO)
async def extrair_dados(
    payload: ExtractionRequestDTO,
    session=Depends(get_session),
    _: AuthenticatedUserEntity = AuthenticatedUser,
):
    # Permite derivar document_ids a partir do solicitation_id quando não enviados
    doc_ids: Optional[List[str]] = payload.document_ids
    if (not doc_ids or len(doc_ids) == 0) and payload.solicitation_id:
        from src.infra.database.repositories.document_repository import (
            DocumentRepository,
        )

        repo = DocumentRepository(session)
        docs = repo.list_by_solicitation(payload.solicitation_id)
        doc_ids = [d.document_id for d in docs]

    if not doc_ids:
        response = GeneralResponseDTO(
            errors=[
                {
                    "message": "Informe 'document_ids' ou um 'solicitation_id' válido com documentos.",
                }
            ]
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(),
        )

    use_case: ExtrairDadosUseCase = create_extrair_dados_use_case(session)
    result = use_case.execute(doc_ids)
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
    use_case: EvaluateEligibilityUseCase = create_avaliar_elegibilidade_use_case(
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


@router.get(
    "/{solicitacao_id}",
    response_model=GeneralResponseDTO,
    summary="Recupera os detalhes de uma solicitação",
)
async def get_solicitacao_by_id(
    solicitacao_id: str,
    session=Depends(get_session),
    _: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case = create_get_solicitacao_by_id_use_case(session)
    try:
        result = use_case.execute(solicitacao_id)
    except Exception:  # pylint: disable=broad-except
        response = GeneralResponseDTO(
            errors=[{"message": "Erro interno ao recuperar a solicitação."}]
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )

    if result.is_left():
        error = result.get_left()
        if isinstance(error, InvalidInputError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(error, SolicitationNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, DomainError):
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(status_code=status_code, content=response.model_dump())

    details = result.get_right()
    dto = SolicitacaoMapper.solicitation_to_dto(details)
    return GeneralResponseDTO(data=dto.model_dump())
