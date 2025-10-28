import re
from typing import List
from pydantic import BaseModel, field_validator, Field


class LegalCaseRequestDTO(BaseModel):
    """DTO para a requisição de consulta de processos."""

    process_numbers: List[str] = Field(
        ...,
        description="Lista de números de processo no formato CNJ (20 dígitos).",
        examples=[["08011255320238100022", "07108025520188020001"]],
    )

    @field_validator("process_numbers")
    @classmethod
    def validate_process_numbers(cls, numbers: List[str]) -> List[str]:
        """Valida se cada número na lista tem exatamente 20 dígitos."""

        cnj_pattern = re.compile(r"^\d{20}$")

        if not numbers:
            raise ValueError("A lista de números de processo não pode estar vazia.")

        for num in numbers:
            if not cnj_pattern.match(num):
                raise ValueError(
                    f"O número '{num}' é inválido. Deve conter exatamente 20 dígitos."
                )

        return numbers
