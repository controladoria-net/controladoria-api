from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GeneralResponseDTO(BaseModel):
    """DTO de resposta padrão para todos os endpoints da API."""

    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True
