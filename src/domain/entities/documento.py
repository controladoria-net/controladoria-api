from dataclasses import dataclass
from .categorias import CategoriaDocumento
import os


@dataclass(frozen=True)
class DocumentoProcessar:
    caminho_temporario: str
    nome_arquivo_original: str

    @property
    def formato_arquivo(self) -> str:
        _, extension = os.path.splitext(self.nome_arquivo_original)
        return extension.replace('.', '').upper()
    

@dataclass(frozen=True)
class ResultadoClassificacao:
    categoria: CategoriaDocumento
    nome_arquivo: str
    formato_arquivo: str

