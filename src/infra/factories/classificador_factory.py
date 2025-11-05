from domain.usecases.classificar_documentos_usecase import ClassificarDocumentosUseCase
from domain.gateway.classificador_gateway import IClassificadorGateway
from infra.external.gateway.gemini_classificador_gateway import GeminiClassificadorGateway
from typing import Optional

_gateway_instance: Optional[IClassificadorGateway] = None

def get_classificador_gateway() -> IClassificadorGateway:
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = GeminiClassificadorGateway()
        try:
            _gateway_instance.configurar() 
        except ValueError as e:
            _gateway_instance = None 
            raise
    return _gateway_instance

def create_classificar_documentos_usecase() -> ClassificarDocumentosUseCase:
    gateway = get_classificador_gateway()
    usecase = ClassificarDocumentosUseCase(classificador_gateway=gateway)
    return usecase