from domain.gateway.legal_case_gateway import LegalCaseGateway
from infra.external.gateway.datajud_gateway import DataJudGateway


def create_legal_case_gateway() -> LegalCaseGateway:
    return DataJudGateway()
