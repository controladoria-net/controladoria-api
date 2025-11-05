from typing import Any, Optional
from src.domain.entities.documento import ResultadoClassificacao
from src.domain.entities.categorias import CategoriaDocumento


class ClassificacaoMapper:
    @staticmethod
    def to_domain(
        response_dto, documento, mimetype: Optional[Any], gemini_file: str | None = None
    ):
        classificacao_raw = getattr(response_dto.classificacao, "type", None)

        if isinstance(classificacao_raw, str):
            valor = classificacao_raw.strip().upper()
            try:
                classificacao_enum = CategoriaDocumento[valor]
            except KeyError:
                try:
                    classificacao_enum = CategoriaDocumento(valor)
                except Exception:
                    classificacao_enum = CategoriaDocumento.OUTRO
        elif isinstance(classificacao_raw, CategoriaDocumento):
            classificacao_enum = classificacao_raw
        else:
            classificacao_enum = CategoriaDocumento.OUTRO

        mimetype_final = mimetype or documento.mimetype
        if isinstance(mimetype_final, str) and not mimetype_final.startswith(
            "application/"
        ):
            mimetype_final = (
                f"application/{mimetype_final.lower().replace('application/', '')}"
            )

        # Preserve original file name in 'arquivo' so that HTTP mapper can
        # correlate with persisted metadata keyed by the original filename.
        return ResultadoClassificacao(
            classificacao=classificacao_enum,
            confianca=float(getattr(response_dto.classificacao, "confidence", 0.0)),
            arquivo=documento.nome_arquivo_original,
            mimetype=mimetype_final,
        )
