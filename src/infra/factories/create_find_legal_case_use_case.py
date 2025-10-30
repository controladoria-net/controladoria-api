from src.infra.external.gateway.datajud_gateway import DataJudGateway
from src.domain.usecases.find_legal_case_use_case import FindLegalCaseUseCase


def create_find_legal_case_use_case() -> FindLegalCaseUseCase:
    return FindLegalCaseUseCase(gateway=DataJudGateway())
