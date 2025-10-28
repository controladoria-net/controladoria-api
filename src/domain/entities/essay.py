from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class EssayStatus(Enum):
    VALID = "valid"
    THEME_DEVIATION = "theme_deviation"
    COPY = "copy"
    EMPTY = "empty"
    INSUFFICIENT = "insufficient"


@dataclass
class Essay:
    text: str

    total_score: Optional[float] = None
    competence_1: Optional[float] = None
    competence_2: Optional[float] = None
    competence_3: Optional[float] = None
    competence_4: Optional[float] = None
    competence_5: Optional[float] = None

    status: EssayStatus = EssayStatus.VALID

    feedback: Optional[List[str]] = None

    def __post_init__(self):
        if self.total_score is not None and not 0 <= self.total_score <= 1000:
            raise ValueError("Nota total deve estar entre 0 e 1000")

        for comp in [
            self.competence_1,
            self.competence_2,
            self.competence_3,
            self.competence_4,
            self.competence_5,
        ]:
            if comp is not None and not 0 <= comp <= 200:
                raise ValueError("Notas das competências devem estar entre 0 e 200")

    @property
    def is_valid(self) -> bool:
        return self.status == EssayStatus.VALID and len(self.text.strip()) > 0

    @property
    def competence_scores(self) -> List[Optional[float]]:
        return [
            self.competence_1,
            self.competence_2,
            self.competence_3,
            self.competence_4,
            self.competence_5,
        ]

    def calculate_total_from_competences(self) -> float:
        scores = [score for score in self.competence_scores if score is not None]
        if len(scores) != 5:
            raise ValueError("Todas as competências devem ter nota para calcular total")
        return sum(scores)
