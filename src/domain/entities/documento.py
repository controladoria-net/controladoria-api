from dataclasses import dataclass
from domain.entities.categorias import CategoriaDocumento
import os
from typing import Any


@dataclass(frozen=True)
class DocumentoProcessar:
    """
    Representa um documento pronto para ser processado.
    Contém um file-like object (stream) em vez de um path.
    """
    file_object: Any              # <-- Alterado: Armazena o stream (file-like object)
    nome_arquivo_original: str
    mimetype: str

    def get_formato(self) -> str:
        """Extrai a extensão do nome original."""
        _, extension = os.path.splitext(self.nome_arquivo_original)
        return extension.replace('.', '').lower()

@dataclass(frozen=True)
class ResultadoClassificacao:
    """
    Representa o resultado da classification de um único documento.
    Atualizado para conter os novos campos solicitados.
    """
    classificacao: CategoriaDocumento  # O Enum da categoria
    confianca: float                  # O score de confiança (ex: 0.95)
    arquivo: str                      # O nome original do arquivo
    mimetype: str                     # O mimetype (ex: 'application/pdf')              


