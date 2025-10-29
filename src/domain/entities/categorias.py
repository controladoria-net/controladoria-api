from enum import Enum

class CategoriaDocumento(str, Enum):
    CERTIFICADO_DE_REGULARIDADE = "CERTIFICADO_DE_REGULARIDADE"
    CAEPF = "CAEPF"
    DECLARACAO_DE_RESIDENCIA = "DECLARAÇÃO_DE_RESIDÊNCIA"
    CNIS = "CNIS"
    TERMO_DE_REPRESENTACAO = "TERMO_DE_REPRESENTAÇÃO"
    PROCURACAO = "PROCURAÇÃO"
    GPS_E_COMPROVANTE = "GPS_E_COMPROVANTE"
    BIOMETRIA = "BIOMETRIA"
    CIN = "CIN"
    CPF = "CPF"
    REAP = "REAP"
    
    OUTRO = "OUTRO"
    ERRO_NA_CLASSIFICACAO = "ERRO_NA_CLASSIFICACAO"
    ERRO_DE_FORMATO = "ERRO_DE_FORMATO"
    ERRO_NO_PROCESSAMENTO_DA_API = "ERRO_NO_PROCESSAMENTO_DA_API"

    @classmethod
    def _missing_(cls, value):
        #print(f"Aviso: Categoria desconhecida recebida: '{value}'. Classificando como OUTRO.")
        return cls.OUTRO
