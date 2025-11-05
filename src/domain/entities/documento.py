from dataclasses import dataclass
from domain.entities.categorias import CategoriaDocumento
import os
from typing import Any


@dataclass(frozen=True)
class DocumentoProcessar:
    file_object: Any       
    nome_arquivo_original: str
    mimetype: str

    def get_formato(self) -> str:
        _, extension = os.path.splitext(self.nome_arquivo_original)
        return extension.replace('.', '').lower()

@dataclass(frozen=True)
class ResultadoClassificacao:
    classificacao: CategoriaDocumento 
    confianca: float                  
    arquivo: str              
    mimetype: str                               


