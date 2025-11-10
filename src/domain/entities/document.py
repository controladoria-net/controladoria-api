from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class DocumentMetadata:
    """Data class representing stored document metadata."""

    def __init__(
        self,
        document_id: str,
        solicitation_id: str,
        s3_key: str,
        mimetype: str,
        classification: Optional[str] = None,
        file_name: Optional[str] = None,
        uploaded_at: Optional[datetime] = None,
    ) -> None:
        self.document_id = document_id
        self.solicitation_id = solicitation_id
        self.s3_key = (
            s3_key  # TODO: remover, pois está muito atrelado à integração com S3
        )
        self.mimetype = mimetype
        self.classification = classification
        self.file_name = file_name
        self.uploaded_at = uploaded_at


class DocumentClassification(str, Enum):
    CERTIFICADO_DE_REGULARIDADE = "CERTIFICADO_DE_REGULARIDADE"
    CAEPF = "CAEPF"
    DECLARACAO_DE_RESIDENCIA = "DECLARACAO_DE_RESIDENCIA"
    CNIS = "CNIS"
    TERMO_DE_REPRESENTACAO = "TERMO_DE_REPRESENTACAO"
    PROCURACAO = "PROCURACAO"
    GPS_E_COMPROVANTE = "GPS_E_COMPROVANTE"
    BIOMETRIA = "BIOMETRIA"
    CIN = "CIN"
    CPF = "CPF"
    REAP = "REAP"
    OUTRO = "OUTRO"

    @classmethod
    def _missing_(cls, value):
        return cls.OUTRO


@dataclass
class ClassificationDocument:
    data: bytes
    mimetype: str
    name: str
