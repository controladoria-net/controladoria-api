from typing import List, Dict
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao
from domain.entities.categorias import CategoriaDocumento
from domain.gateway.classificador_gateway import IClassificadorGateway

class ClassificarDocumentosUseCase:
    def __init__(self, classificador_gateway: IClassificadorGateway):
        """
        Inicializa o Usecase injetando a dependência do gateway.
        """
        if not isinstance(classificador_gateway, IClassificadorGateway):
            raise ValueError("gateway deve ser uma instância de IClassificadorGateway")
        self.classificador_gateway = classificador_gateway

    def executar(self, documentos: List[DocumentoProcessar]) -> Dict[str, List[ResultadoClassificacao]]:
        """
        Executa o caso de uso.
        
        1. Itera sobre os documentos.
        2. Chama o gateway para classificar cada um.
        3. Agrupa os resultados por categoria.
        """
        if not documentos:
            raise ValueError("Nenhum documento fornecido para processamento.")

        print(f"Use Case: Iniciando processamento de {len(documentos)} documentos.")

        resultados_agrupados: Dict[str, List[ResultadoClassificacao]] = {}

        for i, documento in enumerate(documentos):
            print(f"Use Case: Processando [{i+1}/{len(documentos)}] {documento.nome_arquivo_original}...")
            try:
                # 2. Chama o gateway
                resultado = self.classificador_gateway.classificar(documento)
                
                # Acessa o novo campo 'classificacao'
                categoria_str = resultado.classificacao.value

            except Exception as e:
                # Captura erros durante a classificação (ex: falha na API externa)
                print(f"Use Case: Erro ao classificar {documento.nome_arquivo_original}: {e}")
                categoria_str = CategoriaDocumento.ERRO_NA_CLASSIFICACAO.value
                # Cria a entidade de erro com a nova estrutura
                resultado = ResultadoClassificacao(
                    classificacao=CategoriaDocumento.ERRO_NA_CLASSIFICACAO,
                    confianca=0.0,
                    arquivo=documento.nome_arquivo_original,
                    mimetype=documento.mimetype
                )
            
            # 3. Agrupa os resultados
            if categoria_str not in resultados_agrupados:
                resultados_agrupados[categoria_str] = []
            
            resultados_agrupados[categoria_str].append(resultado)

        print("Use Case: Processamento do lote concluído.")
        return resultados_agrupados