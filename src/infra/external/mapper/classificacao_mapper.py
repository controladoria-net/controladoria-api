from typing import Any, Optional
from domain.entities.documento import ResultadoClassificacao, DocumentoProcessar
from domain.entities.categorias import CategoriaDocumento
from infra.external.dto.gemini_dto import GeminiResponseDTO


from domain.entities.categorias import CategoriaDocumento

class ClassificacaoMapper:
    @staticmethod
    def to_domain(response_dto, documento, mimetype: Optional[Any], gemini_file: str | None = None):
        # Obtém o nome da classificação vinda do DTO (string)
        classificacao_raw = response_dto.classificacao.type

        # 🔹 Converte para Enum CategoriaDocumento, se for string
        if isinstance(classificacao_raw, str):
            try:
                classificacao_enum = CategoriaDocumento[classificacao_raw.upper()]
            except KeyError:
                # fallback para caso o modelo retorne algo desconhecido
                classificacao_enum = CategoriaDocumento.ERRO_NAO_RECONHECIDO
        else:
            classificacao_enum = classificacao_raw

        return ResultadoClassificacao(
            classificacao=classificacao_enum,
            confianca=response_dto.classificacao.confidence,
            arquivo=gemini_file or documento.nome_arquivo_original,
            mimetype=mimetype or documento.mimetype,
        )
