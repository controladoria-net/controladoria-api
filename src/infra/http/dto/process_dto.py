from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class LegalCaseMovementDTO(BaseModel):
    """Movement entry for a legal case."""

    date: datetime
    description: str


class LegalCaseResponseDTO(BaseModel):
    """DTO representing a legal case returned to the client."""

    numero_processo: str
    tribunal: Optional[str] = None
    orgao_julgador: Optional[str] = None
    classe_processual: Optional[str] = None
    assunto: Optional[str] = None
    situacao: Optional[str] = None
    data_ajuizamento: Optional[datetime] = None
    movimentacoes: int = 0
    ultima_movimentacao: Optional[datetime] = None
    ultima_movimentacao_descricao: Optional[str] = None
    prioridade: str
    status: Optional[str] = None
    movement_history: Optional[List[LegalCaseMovementDTO]] = None


class DashboardCountItem(BaseModel):
    label: str
    value: int


class DashboardPeriodItem(BaseModel):
    period: str
    value: int


class DashboardCaseHighlight(BaseModel):
    numero_processo: str
    tribunal: Optional[str] = None
    movimentacoes: int
    ultima_movimentacao: Optional[datetime] = None


class ProcessDashboardDTO(BaseModel):
    """Dashboard payload for processes."""

    status_count: Dict[str, int]
    by_court: List[DashboardCountItem]
    by_period: List[DashboardPeriodItem]
    period_granularity: str
    avg_time_between_movements_days: float
    top_by_movements: List[DashboardCaseHighlight]
    last_updated_list: List[DashboardCaseHighlight]
