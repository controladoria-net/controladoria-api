from pydantic import BaseModel, Field
from typing import Optional

class GeminiResponseDTO(BaseModel):
    """
    Valida o JSON esperado da API do Gemini.
    """
    categoria: str
    formato_arquivo: Optional[str] = Field(None, alias="formato_arquivo") # O prompt pede, mas o nome do arquivo já temos
    nome_arquivo: Optional[str] = Field(None, alias="nome_arquivo") # O prompt pede, mas o nome do arquivo já temos
