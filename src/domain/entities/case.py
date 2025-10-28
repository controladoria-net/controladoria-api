from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class Movement:
    date: datetime
    description: str


@dataclass
class LegalCase:
    case_number: str
    court: str
    judging_body: str
    procedural_class: str
    subject: str
    status: str
    filing_date: datetime
    latest_update: str
    movement_history: List[Movement]
