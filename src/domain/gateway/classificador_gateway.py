from abc import ABC, abstractmethod
from src.domain.entities.documento import DocumentoProcessar, ResultadoClassificacao


class IClassificadorGateway(ABC):
    @abstractmethod
    def configurar(self):
        pass

    @abstractmethod
    def classificar(self, documento: DocumentoProcessar) -> ResultadoClassificacao:
        pass
