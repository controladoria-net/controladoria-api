from dataclasses import dataclass
import re
from typing import Optional, List
from datetime import datetime

PATTERN = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")


def format_cnj_number(raw_number: str) -> str:
    if not re.match(r"^\d{20}$", raw_number):
        raise ValueError("Input must be a string with exactly 20 digits.")
    # NNNNNNN (Número Sequencial do Processo)
    sequential_number = raw_number[0:7]
    # DD (Dígito Verificador)
    check_digit = raw_number[7:9]
    # AAAA (Ano de Ajuizamento)
    year = raw_number[9:13]
    # J (Segmento do Judiciário)
    judiciary_branch = raw_number[13:14]
    # TR (Tribunal ou Região)
    court_code = raw_number[14:16]
    # OOOO (Unidade de Origem)
    origin_unit = raw_number[16:20]

    return (
        f"{sequential_number}-{check_digit}.{year}."
        f"{judiciary_branch}.{court_code}.{origin_unit}"
    )


@dataclass(frozen=True)
class CNJNumber:
    number: str

    @classmethod
    def from_raw(cls, raw_number: str) -> "CNJNumber":
        formatted_number = format_cnj_number(raw_number)
        return cls(number=formatted_number)

    def __post_init__(self):
        if not PATTERN.match(self.number):
            raise ValueError("Invalid CNJ number format after formatting.")

    @property
    def judiciary_branch_code(self) -> str:
        return self.number[16]

    @property
    def court_code(self) -> str:
        return self.number[18:20]

    @property
    def year(self) -> str:
        return self.number[11:15]

    @property
    def clean_number(self) -> str:
        return re.sub(r"[^\d]", "", self.number)


@dataclass
class Movement:
    date: datetime
    description: str


@dataclass
class LegalCase:
    case_number: Optional[str]
    court: Optional[str]
    judging_body: Optional[str]
    procedural_class: Optional[str]
    subject: Optional[str]
    status: Optional[str]
    filing_date: Optional[datetime]
    latest_update: Optional[str]
    movement_history: Optional[List[Movement]]
