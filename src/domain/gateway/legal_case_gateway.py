from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.case import CNJNumber, LegalCase


class LegalCaseGateway(ABC):
    @abstractmethod
    def find_case_by_number(
        self, case_number: CNJNumber, court_acronym: str
    ) -> Optional[LegalCase]:
        pass
