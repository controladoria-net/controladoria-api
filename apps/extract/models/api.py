from pathlib import Path
from enum import StrEnum
from typing import Any, Dict, Optional

from pydantic import BaseModel

from models.document import Type


class GeminiModels(StrEnum):
    GEMINI_FLASH_2_0 = "gemini-2.0-flash"
    # Add other models as needed ...


class GetDocumentMetadataRequest(BaseModel):
    model: GeminiModels = GeminiModels.GEMINI_FLASH_2_0
    content: str | Path
    type: Type
    content_mime_type: Optional[str] = None
    temperature: Optional[float] = None


class DocumentMetadataResponse(BaseModel):
    type: Type
    data: Dict[str, Any]
    raw: Dict[str, Any]












