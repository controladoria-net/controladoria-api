from typing import List, Dict
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento
from domain.gateway.classificador_gateway import IClassificadorGateway

class ClassificarDocumentosUseCase:
    def __init__(self, classificador_gateway: IClassificadorGateway):
        if not isinstance(classificador_gateway, IClassificadorGateway):
            raise ValueError("gateway deve ser uma instância de IClassificadorGateway")
        self.classificador_gateway = classificador_gateway

    def executar(self, documentos: List[DocumentoProcessar]) -> Dict[str, List[ResultadoClassificacao]]:
        if not documentos:
            raise ValueError("Nenhum documento fornecido para processamento.")

        resultados_agrupados: Dict[str, List[ResultadoClassificacao]] = {}

        for i, documento in enumerate(documentos):
            try:
                resultado = self.classificador_gateway.classificar(documento)
                
                categoria_str = resultado.classificacao.value

            except Exception as e:
                categoria_str = CategoriaDocumento.ERRO_NA_CLASSIFICACAO.value
                resultado = ResultadoClassificacao(
                    classificacao=CategoriaDocumento.ERRO_NA_CLASSIFICACAO,
                    confianca=0.0,
                    arquivo=documento.nome_arquivo_original,
                    mimetype=documento.mimetype
                )
            
            if categoria_str not in resultados_agrupados:
                resultados_agrupados[categoria_str] = []
            
            resultados_agrupados[categoria_str].append(resultado)

        return resultados_agrupados