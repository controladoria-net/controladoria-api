from abc import ABC, abstractmethod
from domain.entities.documento import DocumentoProcessar, ResultadoClassificacao

class IClassificadorGateway(ABC):
    @abstractmethod
    def configurar(self):
        """
        Método para configurar o gateway
        """
        pass

    @abstractmethod
    def classificar(self, documento: DocumentoProcessar) -> ResultadoClassificacao:
        """
        Recebe uma entidade DocumentoProcessar e retorna uma entidade 
        ResultadoClassificacao.
        """
        pass