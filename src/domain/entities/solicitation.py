from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SolicitationDocument:
    """Lightweight projection of a solicitation document."""

    id: str
    file_name: Optional[str]
    mimetype: str
    classification: Optional[str]
    confidence: Optional[float]
    uploaded_at: Optional[datetime]


@dataclass(frozen=True)
class SolicitationDetails:
    """Aggregate view for a solicitation."""

    id: str
    pescador: Optional[Dict[str, object]]
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    analysis: Optional[Dict[str, object]]
    lawyer_notes: Optional[str]
    documents: List[SolicitationDocument]
