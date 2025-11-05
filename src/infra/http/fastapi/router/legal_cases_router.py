from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from src.domain.core.errors import (
    ExternalRateLimitError,
    InvalidInputError,
    LegalCaseNotFoundError,
)
from src.domain.entities.auth import AuthenticatedUserEntity
from src.domain.usecases.build_process_dashboard_use_case import (
    BuildProcessDashboardUseCase,
)
from src.domain.usecases.get_legal_case_by_id_use_case import GetLegalCaseByIdUseCase
from src.infra.database.session import get_session
from src.infra.factories.legal_case_factories import (
    create_get_legal_case_by_id_use_case,
    create_process_dashboard_use_case,
)
from src.infra.http.dto.general_response_dto import GeneralResponseDTO
from src.infra.http.mapper.process_mapper import ProcessMapper
from src.infra.http.security.auth_decorator import AuthenticatedUser

router = APIRouter(prefix="/processos", tags=["Processos"])


@router.get("/consultar/{case_number}", response_model=GeneralResponseDTO)
def consultar_processo(
    case_number: str,
    session=Depends(get_session),
    current_user: AuthenticatedUserEntity = AuthenticatedUser,
):
    use_case: GetLegalCaseByIdUseCase = create_get_legal_case_by_id_use_case(session)
    result = use_case.execute(case_number)
    if result.is_left():
        error = result.get_left()
        if isinstance(error, InvalidInputError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(error, LegalCaseNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, ExternalRateLimitError):
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(status_code=status_code, content=response.model_dump())

    persisted = result.get_right()
    dto = ProcessMapper.case_to_dto(persisted)
    return GeneralResponseDTO(data=dto.model_dump())


@router.get("/dashboard", response_model=GeneralResponseDTO)
def dashboard_processos(
    session=Depends(get_session),
    current_user: AuthenticatedUserEntity = AuthenticatedUser,
    status_filter: list[str] | None = Query(default=None, alias="status"),
    priority: list[str] | None = Query(default=None),
    tribunal: list[str] | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort_field: str | None = Query(default=None),
    sort_dir: str = Query(default="desc"),
):
    use_case: BuildProcessDashboardUseCase = create_process_dashboard_use_case(session)
    result = use_case.execute(
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        priority=priority,
        tribunal=tribunal,
        sort_field=sort_field,
        sort_direction=sort_dir,
    )
    if result.is_left():
        error = result.get_left()
        response = GeneralResponseDTO(errors=[{"message": error.message}])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(),
        )

    aggregation = result.get_right()
    dto = ProcessMapper.dashboard_to_dto(aggregation.data)
    return GeneralResponseDTO(data=dto.model_dump())
