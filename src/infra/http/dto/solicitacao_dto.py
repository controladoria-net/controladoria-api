from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class DocumentDTO(BaseModel):
    """Document metadata for a solicitation."""

    id: str
    fileName: Optional[str] = None
    mimetype: str
    classification: Optional[str] = None
    confidence: Optional[float] = None
    uploadedAt: Optional[datetime] = None


class SolicitacaoDTO(BaseModel):
    """DTO representing a solicitation detail response."""

    id: str
    pescador: Optional[Dict[str, object]] = None
    status: str
    documents: List[DocumentDTO]
    analysis: Optional[Dict[str, object]] = None
    createdAt: datetime
    updatedAt: datetime
    lawyerNotes: Optional[str] = None
    priority: str


class ClassificationResultDTO(BaseModel):
    """Classification summary for a document."""

    document_id: str
    categoria: str
    confianca: float
    arquivo: str
    mimetype: str


class ClassificationGroupDTO(BaseModel):
    categoria: str
    documentos: List[ClassificationResultDTO]


class ClassificationResponseDTO(BaseModel):
    """Response payload for document classification."""

    solicitation_id: str
    groups: List[ClassificationGroupDTO]


class ExtractionItemDTO(BaseModel):
    document_id: str
    document_type: str
    extracted: Dict[str, object]


class ExtractionResponseDTO(BaseModel):
    solicitation_id: str
    items: List[ExtractionItemDTO]


class EligibilityResponseDTO(BaseModel):
    solicitation_id: str
    status: str
    score_texto: str
    pendencias: List[str]
    evaluated_at: datetime


class SolicitationDashboardDTO(BaseModel):
    status_count: Dict[str, int]
    by_period: List[Dict[str, object]]
    period_granularity: str
    avg_processing_time_days: float
    approval_rate: float
    most_missing_documents: List[Dict[str, object]]
