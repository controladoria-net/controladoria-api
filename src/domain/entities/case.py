from dataclasses import dataclass
import re
from typing import List
from datetime import datetime


def format_cnj_number(clean_number: str) -> str:
    """Formats a 20-digit string into the standard CNJ format."""
    if not re.match(r"^\d{20}$", clean_number):
        raise ValueError("Input must be a string with exactly 20 digits.")
    p1 = clean_number[0:7]
    p2 = clean_number[7:9]
    p3 = clean_number[9:13]
    p4 = clean_number[13:14]
    p5 = clean_number[14:16]
    p6 = clean_number[16:20]
    return f"{p1}-{p2}.{p3}.{p4}.{p5}.{p6}"


@dataclass(frozen=True)
class CNJNumber:
    """A Value Object representing a validated CNJ legal case number."""

    number: str

    @classmethod
    def from_raw(cls, raw_number: str) -> "CNJNumber":
        """Factory method to create an instance from a raw 20-digit string."""
        formatted_number = format_cnj_number(raw_number)
        return cls(number=formatted_number)

    def __post_init__(self):
        """Validates the formatted number after the object is created."""
        pattern = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
        if not pattern.match(self.number):
            # This validation is a safeguard, but format_cnj_number should prevent this.
            raise ValueError("Invalid CNJ number format after formatting.")

    @property
    def judiciary_branch_code(self) -> str:
        """Returns the 'J' part (e.g., '8' for State Court)."""
        return self.number[16]

    @property
    def court_code(self) -> str:
        """Returns the 'TR' part (e.g., '10' for TJMA)."""
        return self.number[18:20]

    @property
    def year(self) -> str:
        return self.number[11:15]

    @property
    def clean_number(self) -> str:
        """Returns the number as a 20-digit string."""
        return re.sub(r"[^\d]", "", self.number)


@dataclass
class Movement:
    date: datetime
    description: str


@dataclass
class LegalCase:
    case_number: CNJNumber
    court: str
    judging_body: str
    procedural_class: str
    subject: str
    status: str
    filing_date: datetime
    latest_update: str
    movement_history: List[Movement]
