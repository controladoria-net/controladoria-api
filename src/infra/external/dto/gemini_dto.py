from pydantic import BaseModel, Field
from typing import Optional


class ClassificacaoDTO(BaseModel):
    type: str = Field(..., description="A categoria do documento classificado.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança da classificação (0.0 a 1.0).")


class GeminiResponseDTO(BaseModel):
    classificacao: ClassificacaoDTO
    mimetype: Optional[str] = Field(None, description="Tipo MIME inferido pelo modelo (opcional).")