from typing import Any, Optional
from domain.entities.documento import ResultadoClassificacao, DocumentoProcessar
from domain.entities.categorias import CategoriaDocumento
from infra.external.dto.gemini_dto import GeminiResponseDTO


class ClassificacaoMapper:
    @staticmethod
    def to_domain(response_dto, documento, mimetype: Optional[Any], gemini_file: str | None = None):
        # Obtém o nome da classificação vinda do DTO (string ou Enum)
        classificacao_raw = getattr(response_dto.classificacao, "type", None)

        # 🔹 Tenta converter para Enum CategoriaDocumento
        if isinstance(classificacao_raw, str):
            valor = classificacao_raw.strip().upper()
            try:
                classificacao_enum = CategoriaDocumento[valor]
            except KeyError:
                try:
                    # tenta via value (caso seja "CAEPF" etc.)
                    classificacao_enum = CategoriaDocumento(valor)
                except Exception:
                    # fallback padrão (substitui o ERRO_NAO_RECONHECIDO)
                    classificacao_enum = CategoriaDocumento.OUTRO
        elif isinstance(classificacao_raw, CategoriaDocumento):
            classificacao_enum = classificacao_raw
        else:
            classificacao_enum = CategoriaDocumento.OUTRO

        # Normaliza o mimetype se precisar
        mimetype_final = mimetype or documento.mimetype
        if isinstance(mimetype_final, str) and not mimetype_final.startswith("application/"):
            mimetype_final = f"application/{mimetype_final.lower().replace('application/', '')}"

        return ResultadoClassificacao(
            classificacao=classificacao_enum,
            confianca=float(getattr(response_dto.classificacao, "confidence", 0.0)),
            arquivo=gemini_file or documento.nome_arquivo_original,
            mimetype=mimetype_final,
        )
