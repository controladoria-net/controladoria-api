from src.infra.external.dto.legal_case_dto import LegalCaseRawDTO
from src.infra.external.mapper.legal_case_mapper import LegalCaseMapper


def test_from_dto_to_domain_preserves_formatted_case_number():
    dto = LegalCaseRawDTO(
        numero_processo="0710802-55.2018.8.02.0001",
    )

    legal_case = LegalCaseMapper.from_dto_to_domain(dto)

    assert legal_case.case_number == "0710802-55.2018.8.02.0001"


def test_from_dto_to_domain_formats_digit_only_case_number():
    dto = LegalCaseRawDTO(
        numero_processo="07108025520188020001",
    )

    legal_case = LegalCaseMapper.from_dto_to_domain(dto)

    assert legal_case.case_number == "0710802-55.2018.8.02.0001"
