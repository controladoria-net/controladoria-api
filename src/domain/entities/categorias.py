from enum import Enum

class CategoriaDocumento(str, Enum):
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
