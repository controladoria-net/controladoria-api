class DomainError(Exception):
    """Base error for the domain layer."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RepositoryError(DomainError):
    """Raised when repositories fail to execute an operation."""

    def __init__(self, message: str = "Falha ao acessar o repositório.") -> None:
        super().__init__(message)


class InvalidCredentialsError(DomainError):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        super().__init__("Credenciais inválidas. Verifique usuário e senha.")


class TokenRefreshError(DomainError):
    """Raised when refresh token flow fails."""

    def __init__(self) -> None:
        super().__init__("Não foi possível atualizar o token. Faça login novamente.")


class TokenValidationError(DomainError):
    """Raised when the access token is invalid or expired."""

    def __init__(self, message: str = "Token de acesso inválido ou expirado.") -> None:
        super().__init__(message)


class LogoutError(DomainError):
    """Raised when the logout operation cannot be completed."""

    def __init__(self, message: str = "Erro ao processar o logout.") -> None:
        super().__init__(message)


class LegalCaseNotFoundError(DomainError):
    """Raised when a legal case cannot be located."""

    def __init__(self, case_number: str) -> None:
        super().__init__(f"Processo '{case_number}' não foi encontrado.")
        self.case_number = case_number


class LegalCasePersistenceError(DomainError):
    """Raised when persisting a legal case fails."""

    def __init__(self, message: str = "Falha ao salvar os dados do processo.") -> None:
        super().__init__(message)


class ExternalRateLimitError(DomainError):
    """Raised when an external dependency signals rate limiting."""

    def __init__(
        self,
        message: str = "Limite de requisições atingido. Tente novamente mais tarde.",
    ) -> None:
        super().__init__(message)


class SolicitationNotFoundError(DomainError):
    """Raised when a solicitation is missing."""

    def __init__(self, solicitation_id: str) -> None:
        super().__init__(f"Solicitação '{solicitation_id}' não foi encontrada.")
        self.solicitation_id = solicitation_id


class DocumentNotFoundError(DomainError):
    """Raised when a document cannot be located."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Documento '{document_id}' não foi encontrado.")
        self.document_id = document_id


class InvalidInputError(DomainError):
    """Raised when user input validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UploadError(DomainError):
    """Raised when an upload attempt fails."""

    def __init__(self, message: str = "Falha ao fazer upload dos documentos.") -> None:
        super().__init__(message)


class StorageError(DomainError):
    """Raised when the storage layer fails."""

    def __init__(self, message: str = "Falha ao armazenar dados.") -> None:
        super().__init__(message)


class ClassificationError(DomainError):
    """Raised when the classification flow fails."""

    def __init__(
        self, message: str = "Não foi possível classificar os documentos."
    ) -> None:
        super().__init__(message)


class ExtractionError(DomainError):
    """Raised when document extraction fails."""

    def __init__(
        self, message: str = "Falha ao extrair os dados do documento."
    ) -> None:
        super().__init__(message)


class UnsupportedDocumentError(DomainError):
    """Raised when a document type is not supported."""

    def __init__(self, document_type: str) -> None:
        super().__init__(f"Documento do tipo '{document_type}' não é suportado.")
        self.document_type = document_type


class IncompleteDataError(DomainError):
    """Raised when required data for processing is missing."""

    def __init__(
        self, message: str = "Dados insuficientes para concluir a operação."
    ) -> None:
        super().__init__(message)


class EligibilityComputationError(DomainError):
    """Raised when eligibility computation encounters an unexpected issue."""

    def __init__(self, message: str = "Erro ao calcular a elegibilidade.") -> None:
        super().__init__(message)
