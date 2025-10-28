from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LegalCaseGateway(ABC):
    @abstractmethod
    def find_case_by_number(self, case_number: str) -> Optional[Dict[str, Any]]:
        pass
