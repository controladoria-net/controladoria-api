from pathlib import Path
from enum import StrEnum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from models.document import Type


class GeminiModels(StrEnum):
    GEMINI_FLASH_2_0 = "gemini-2.0-flash"
    # Add other models as needed ...


class GetDocumentMetadataRequest(BaseModel):
    model: GeminiModels = GeminiModels.GEMINI_FLASH_2_0
    content: Union[str, Path, List[Union[str, Path]]]
    type: Type
    content_mime_type: Optional[Union[str, List[Optional[str]]]] = None
    temperature: Optional[float] = None
    source_filenames: Optional[List[str]] = None


class DocumentMetadataResponse(BaseModel):
    type: Type
    title: str
    data: Dict[str, Any]
    raw: Dict[str, Any]
    source_files: List[str]


class DocumentMetadataBatchResponse(BaseModel):
    data_files: Dict[str, DocumentMetadataResponse]












