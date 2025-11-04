from domain.usecases.classificar_documentos_usecase import ClassificarDocumentosUseCase
from domain.gateway.classificador_gateway import IClassificadorGateway
from infra.external.gateway.gemini_classificador_gateway import GeminiClassificadorGateway
from typing import Optional

# Cache para o gateway (Singleton)
_gateway_instance: Optional[IClassificadorGateway] = None

def get_classificador_gateway() -> IClassificadorGateway:
    """
    Retorna uma instância singleton do Gateway de Classificação.
    Configura na primeira chamada.
    """
    global _gateway_instance
    if _gateway_instance is None:
        print("Factory: Criando nova instância do GeminiClassificadorGateway...")
        _gateway_instance = GeminiClassificadorGateway()
        try:
            _gateway_instance.configurar() # Configura a API key
        except ValueError as e:
            print(f"Factory: ERRO CRÍTICO - Falha ao configurar o gateway: {e}")
            # Em uma app real, isso poderia impedir a API de iniciar
            _gateway_instance = None # Reseta para tentar de novo na próxima req
            raise
    return _gateway_instance

def create_classificar_documentos_usecase() -> ClassificarDocumentosUseCase:
    """
    Cria e retorna uma instância do ClassificarDocumentosUseCase,
    injetando o gateway concreto.
    """
    print("Factory: Criando Usecase 'ClassificarDocumentosUseCase'...")
    gateway = get_classificador_gateway()
    usecase = ClassificarDocumentosUseCase(classificador_gateway=gateway)
    return usecase