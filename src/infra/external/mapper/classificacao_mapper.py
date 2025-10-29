from domain.entities.documento import ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento
from ..dto.gemini_dto import GeminiResponseDTO

class ClassificacaoMapper:
    @staticmethod
    def to_domain(
        response_dto: GeminiResponseDTO, 
        documento_original_nome: str, 
        documento_original_formato: str
    ) -> ResultadoClassificacao:
        
        # Converte a string da categoria para o Enum, tratando casos desconhecidos
        categoria_enum = CategoriaDocumento(response_dto.categoria)
        
        return ResultadoClassificacao(
            categoria=categoria_enum,
            nome_arquivo=documento_original_nome,
            formato_arquivo=documento_original_formato
        )
