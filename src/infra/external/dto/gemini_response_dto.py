from pydantic import BaseModel, Field, field_validator
from typing import Any, List, Optional, Annotated, Literal
from datetime import date

from src.domain.entities.document import DocumentClassification


class _Endereco(BaseModel):
    cep: Annotated[
        Optional[str],
        Field(None, description="CEP do endereço contido no documento, ex: 01310-100"),
    ]
    logradouro: Annotated[
        str,
        Field(
            ..., description="Nome da rua contida no documento, ex: Avenida Paulista"
        ),
    ]
    numero: Annotated[
        Optional[str],
        Field(None, description="Número do endereço contido no documento, ex: 1000"),
    ]
    complemento: Annotated[
        Optional[str],
        Field(
            None, description="Complemento do endereço, ex: bloco A, apartamento 101"
        ),
    ]
    bairro: Annotated[
        str,
        Field(
            ..., description="Bairro do endereço contido no documento, ex: Bela Vista"
        ),
    ]
    municipio: Annotated[
        str,
        Field(
            ..., description="Cidade do endereço contido no documento, ex: São Paulo"
        ),
    ]
    uf: Annotated[
        str,
        Field(
            ...,
            description="Sigla do estado do endereço contido no documento (ex: SP, RJ)",
            min_length=2,
            max_length=2,
        ),
    ]


class _VinculoCNIS(BaseModel):
    cnpj: Annotated[
        str,
        Field(
            ...,
            description="CNPJ da empresa vínculada ao trabalhador, no formato ##.###.###/####-??",
        ),
    ]
    razao_social: Annotated[
        str, Field(..., description="Razão social da empresa vínculada ao trabalhador")
    ]
    data_admissao: Annotated[
        date,
        Field(
            ...,
            description="Data de início do vínculo empregatício, no formato AAAA-MM-DD",
        ),
    ]
    data_demissao: Annotated[
        Optional[date],
        Field(
            None,
            description="Data de término do vínculo empregatício, no formato AAAA-MM-DD. Pode ser nulo se o vínculo ainda estiver ativo.",
        ),
    ]
    categoria: Annotated[
        str,
        Field(
            ...,
            description="Categoria do trabalhador no vínculo empregatício, ex: Empregado, Estagiário, etc.",
        ),
    ]
    remuneracao_media: Annotated[
        Optional[float],
        Field(
            None,
            description="Remuneração média mensal recebida pelo trabalhador no vínculo empregatício. Pode ser nulo se a informação não estiver disponível.",
        ),
    ]
    situacao: Annotated[
        Literal["ATIVO", "INATIVO", "SUSPENSO", "OUTRO"],
        Field(..., description="Situação atual do vínculo empregatício do trabalhador"),
    ]


class CNISResponseDTO(BaseModel):
    nome: Annotated[str, Field(..., description="Nome completo do trabalhador")]
    cpf: Annotated[
        str,
        Field(
            ..., description="Número do CPF do trabalhador no formato ###.###.###-##"
        ),
    ]
    data_nascimento: Annotated[
        date,
        Field(
            ..., description="Data de nascimento do trabalhador no formato AAAA-MM-DD"
        ),
    ]
    inscricao: Annotated[
        str, Field(..., description="Número de inscrição do trabalhador no CNIS")
    ]
    tipo_inscricao: Annotated[
        Literal["NIS", "PIS", "PASEP"],
        Field(..., description="Tipo de inscrição do trabalhador no CNIS"),
    ]
    mae: Annotated[
        Optional[str], Field(None, description="Nome completo da mãe do trabalhador")
    ]
    ativo: Annotated[
        bool,
        Field(
            ...,
            description="Indica se o trabalhador está ativo no CNIS, é baseado se há algum vínculo empregatício vigente",
        ),
    ]
    vinculos: Annotated[
        list[_VinculoCNIS],
        Field(..., description="Lista de vínculos empregatícios do trabalhador"),
    ]


class RGPResponseDTO(BaseModel):
    tipo_licenca: Annotated[
        Literal["DEFINITIVA", "PROVISÓRIA"],
        Field(..., description="Tipo de licença do RGP"),
    ]
    nome: Annotated[str, Field(..., description="Nome completo do titular do RG")]
    cpf: Annotated[
        Optional[str],
        Field(
            None, description="Número do CPF do titular do RG no formato ###.###.###-##"
        ),
    ]
    rgp: Annotated[
        str, Field(..., description="Número do Registro Geral de Pesca (RGP),")
    ]
    categoria: Annotated[
        str,
        Field(..., description="Categoria da atividade pesqueira autorizada pelo RGP"),
    ]
    data_nascimento: Annotated[
        date,
        Field(
            ..., description="Data de nascimento do titular do RG no formato AAAA-MM-DD"
        ),
    ]
    data_emissao: Annotated[
        Optional[date],
        Field(None, description="Data de emissão do RGP no formato AAAA-MM-DD"),
    ]
    data_validade: Annotated[
        Optional[date],
        Field(None, description="Data de validade do RGP no formato AAAA-MM-DD"),
    ]
    orgao_emissor: Annotated[
        Optional[str], Field(None, description="Órgão emissor do RGP")
    ]
    filiacao: Annotated[
        Optional[str], Field(None, description="Filiação do titular do RGP")
    ]
    municipio_residencia: Annotated[
        Optional[str],
        Field(None, description="Município de residência do titular do RGP"),
    ]


class CAEPFResponseDTO(BaseModel):
    nome: Annotated[str, Field(..., description="Nome completo do titular do CAEPF")]
    cpf: Annotated[
        str,
        Field(
            ...,
            description="Número do CPF do titular do CAEPF no formato ###.###.###-##",
        ),
    ]
    caepf: Annotated[str, Field(..., description="Número do CAEPF")]
    cnae: Annotated[
        str | list[str], Field(..., description="Código(s) CNAE associado(s) ao CAEPF")
    ]
    data_inscricao: Annotated[
        date, Field(..., description="Data de inscrição no CAEPF no formato AAAA-MM-DD")
    ]
    atividade_economica: Annotated[
        str, Field(..., description="Descrição da atividade econômica exercida")
    ]
    qualificacao: Annotated[
        str, Field(..., description="Qualificação do titular do CAEPF")
    ]
    data_inicio_atividade: Annotated[
        date,
        Field(
            ...,
            description="Data de início da atividade econômica no formato AAAA-MM-DD",
        ),
    ]
    situacao_cadastral: Annotated[
        Literal["ATIVO", "INATIVO", "SUSPENSO", "CANCELADO", "BAIXADO", "OUTRO"],
        Field(..., description="Situação cadastral do CAEPF"),
    ]
    endereco: Annotated[
        _Endereco, Field(..., description="Endereço do titular do CAEPF")
    ]


class ProofOfResidenceResponseDTO(BaseModel):
    nome: Annotated[
        str,
        Field(..., description="Nome completo do titular do comprovante de residência"),
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            None,
            description="Número do CPF do titular do comprovante de residência no formato ###.###.###-##",
        ),
    ]
    endereco: Annotated[
        _Endereco,
        Field(
            ..., description="Endereço completo do titular do comprovante de residência"
        ),
    ]
    data_emissao: Annotated[
        Optional[date],
        Field(
            None,
            description="Data de emissão do comprovante de residência no formato AAAA-MM-DD",
        ),
    ]
    tipo_documento: Annotated[
        Optional[str],
        Field(
            None,
            description="Tipo do documento utilizado como comprovante de residência, ex: Conta de luz, Conta de água, etc.",
        ),
    ]
    emissor: Annotated[
        Optional[str],
        Field(
            None,
            description="Nome da empresa ou entidade emissora do comprovante de residência",
        ),
    ]


class _RepresentanteLegal(BaseModel):
    nome: Annotated[str, Field(..., description="Nome completo do representante legal")]
    orgao_emissor_oab: Annotated[
        Optional[str],
        Field(
            None,
            description="Órgão emissor da OAB do representante legal, ex: OAB/SP, OAB/MA",
        ),
    ]
    numero_oab: Annotated[
        Optional[str], Field(None, description="Número da OAB do representante legal")
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            None,
            description="Número do CPF do representante legal no formato ###.###.###-##",
        ),
    ]


class RepresentationTermResponseDTO(BaseModel):
    nome: Annotated[
        str,
        Field(
            ...,
            description="Nome completo do titular do termo de representação, quem está sendo representado",
        ),
    ]
    estado_civil: Annotated[
        str, Field(..., description="Estado civil do titular do termo de representação")
    ]
    profissao: Annotated[
        str, Field(..., description="Profissão do titular do termo de representação")
    ]
    rg: Annotated[
        str, Field(..., description="Número do RG do titular do termo de representação")
    ]
    cpf: Annotated[
        str,
        Field(
            ...,
            description="Número do CPF do titular do termo de representação no formato ###.###.###-##",
        ),
    ]
    endereco: Annotated[
        _Endereco,
        Field(
            ..., description="Endereço completo do titular do termo de representação"
        ),
    ]
    telefone: Annotated[
        Optional[str],
        Field(
            None, description="Número de telefone do titular do termo de representação"
        ),
    ]
    email: Annotated[
        Optional[str],
        Field(
            None, description="Endereço de e-mail do titular do termo de representação"
        ),
    ]
    contem_assinatura: Annotated[
        bool,
        Field(
            ...,
            description="Indica se o termo de representação está corretamente assinado pelo titular",
        ),
    ]
    representante_legal: Annotated[
        list[_RepresentanteLegal],
        Field(
            ...,
            description="Lista de representantes legais autorizados no termo de representação",
        ),
    ]


class _ComposicaoDocumentoGPS(BaseModel):
    codigo: Annotated[str, Field(..., description="Código da composição do documento")]
    denominacao: Annotated[
        str, Field(..., description="Denominação da composição do documento")
    ]
    principal: Annotated[
        float, Field(..., description="Valor principal da composição do documento")
    ]
    multa: Annotated[
        float, Field(..., description="Valor da multa da composição do documento")
    ]
    juros: Annotated[
        float, Field(..., description="Valor dos juros da composição do documento")
    ]
    total: Annotated[
        float, Field(..., description="Valor total da composição do documento")
    ]


class GPSResponseDTO(BaseModel):
    nome: Annotated[str, Field(..., description="Nome completo do contribuinte")]
    cpf: Annotated[
        str,
        Field(
            ..., description="Número do CPF do contribuinte no formato ###.###.###-##"
        ),
    ]
    competencia: Annotated[
        str,
        Field(..., description="Mês e ano de competência da GPS no formato MM/YYYY"),
    ]
    data_vencimento: Annotated[
        date, Field(..., description="Data de vencimento da GPS no formato AAAA-MM-DD")
    ]
    numero_documento: Annotated[
        str, Field(..., description="Número do documento da GPS")
    ]
    observacoes: Annotated[
        Optional[str],
        Field(None, description="Observações adicionais presentes na GPS, se houver"),
    ]
    valor_total: Annotated[float, Field(..., description="Valor total a ser pago")]
    composicao: Annotated[
        list[_ComposicaoDocumentoGPS],
        Field(..., description="Lista de composições do documento"),
    ]
    comprovante_pagamento: Annotated[
        bool,
        Field(
            None, description="Indica se há um comprovante de pagamento anexado à GPS"
        ),
    ]


class BiometryResponseDTO(BaseModel):
    nome: Annotated[
        Optional[str], Field(..., description="Nome completo do titular da biometria")
    ]
    cpf: Annotated[
        str,
        Field(
            ...,
            description="Número do CPF do titular da biometria no formato ###.###.###-##",
        ),
    ]
    titulo_eleitor: Annotated[
        str,
        Field(..., description="Número do título eleitoral do titular da biometria"),
    ]
    municipio: Annotated[
        Optional[str],
        Field(None, description="Município onde a biometria foi registrada"),
    ]
    estado: Annotated[
        Optional[str], Field(None, description="Estado onde a biometria foi registrada")
    ]
    data_emissao: Annotated[
        Optional[date],
        Field(None, description="Data de emissão da biometria no formato AAAA-MM-DD"),
    ]
    zona: Annotated[
        Optional[str], Field(None, description="Zona eleitoral associada à biometria")
    ]
    secao: Annotated[
        Optional[str], Field(None, description="Seção eleitoral associada à biometria")
    ]
    situacao: Annotated[
        str,
        Field(
            ...,
            description="Situação da biometria, geralmente vem acompanhada da frase 'Seu título eleitorral está ...'",
        ),
    ]

    @field_validator("situacao", mode="before")
    @classmethod
    def _ensure_single_status(cls, value):
        """Gemini às vezes retorna lista/dict; normaliza para string única."""
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
        if isinstance(value, dict):
            for key in ("value", "situacao"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            examples = value.get("examples")
            if isinstance(examples, list):
                for item in examples:
                    if isinstance(item, str) and item.strip():
                        return item.strip()
        if isinstance(value, str):
            return value.strip()
        return value


class DeclaracaoFiliacaoResponseDTO(BaseModel):
    nome: Annotated[
        str,
        Field(..., description="Nome completo do titular da declaração de filiação"),
    ]
    cpf: Annotated[
        str,
        Field(
            ...,
            description="Número do CPF do titular da declaração de filiação no formato ###.###.###-##",
        ),
    ]
    endereco: Annotated[
        _Endereco,
        Field(
            ..., description="Endereço completo do titular da declaração de filiação"
        ),
    ]
    nome_entidade: Annotated[
        str, Field(..., description="Nome da entidade à qual o titular está filiado")
    ]
    cnpj_entidade: Annotated[
        Optional[str],
        Field(
            None,
            description="CNPJ da entidade à qual o titular está filiado, no formato ##.###.###/####-??",
        ),
    ]
    nome_representante: Annotated[
        str, Field(..., description="Nome completo do representante legal da entidade")
    ]
    cpf_representante: Annotated[
        Optional[str],
        Field(
            None,
            description="Número do CPF do representante legal da entidade no formato ###.###.###-##",
        ),
    ]
    endereco_entidade: Annotated[
        _Endereco,
        Field(
            ...,
            description="Endereço completo da entidade à qual o titular está filiado",
        ),
    ]
    municipio_emissao: Annotated[
        str,
        Field(..., description="Município onde a declaração de filiação foi emitida"),
    ]
    delegacia_emissao: Annotated[
        Optional[str],
        Field(
            None,
            description="Delegacia onde a declaração de filiação foi emitida, se aplicável",
        ),
    ]
    data_filiacao: Annotated[
        date,
        Field(
            ...,
            description="Data de filiação do titular à entidade no formato AAAA-MM-DD",
        ),
    ]
    data_emissao: Annotated[
        date,
        Field(
            ...,
            description="Data de emissão da declaração de filiação no formato AAAA-MM-DD",
        ),
    ]


class OtherResponseDTO(BaseModel):
    nome: Annotated[
        Optional[str],
        Field(None, description="Nome extraído do documento, se disponível"),
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            None,
            description="Número do CPF extraído do documento no formato ###.###.###-##, se disponível",
        ),
    ]
    endereco: Annotated[
        Optional[_Endereco],
        Field(None, description="Endereço extraído do documento, se disponível"),
    ]
    orgao_emissor: Annotated[
        Optional[str],
        Field(None, description="Órgão emissor extraído do documento, se disponível"),
    ]
    data_emissao: Annotated[
        Optional[date],
        Field(
            None,
            description="Data de emissão extraída do documento no formato AAAA-MM-DD, se disponível",
        ),
    ]
    tipo_documento: Annotated[
        Optional[str],
        Field(None, description="Tipo do documento extraído, se identificado"),
    ]
    informacoes_adicionais: Annotated[
        Optional[Any],
        Field(None, description="Outras informações relevantes extraídas do documento"),
    ]


class ExtratorResponseDTO(BaseModel):
    cnis: Annotated[
        Optional[CNISResponseDTO],
        Field(None, description="Metadados extraídos de um documento CNIS"),
    ]
    rgp: Annotated[
        Optional[RGPResponseDTO],
        Field(None, description="Metadados extraídos de um documento RGP"),
    ]
    caepf: Annotated[
        Optional[CAEPFResponseDTO],
        Field(None, description="Metadados extraídos de um documento CAEPF"),
    ]
    comprovante_residencia: Annotated[
        Optional[ProofOfResidenceResponseDTO],
        Field(None, description="Metadados extraídos de um comprovante de residência"),
    ]
    termo_representacao: Annotated[
        Optional[RepresentationTermResponseDTO],
        Field(None, description="Metadados extraídos de um termo de representação"),
    ]
    gps: Annotated[
        Optional[GPSResponseDTO],
        Field(None, description="Metadados extraídos de um documento GPS"),
    ]
    biometria: Annotated[
        Optional[BiometryResponseDTO],
        Field(None, description="Metadados extraídos de um documento de biometria"),
    ]
    declaracao_filiacao: Annotated[
        Optional[DeclaracaoFiliacaoResponseDTO],
        Field(None, description="Metadados extraídos de uma declaração de filiação"),
    ]
    other: Annotated[
        Optional[OtherResponseDTO],
        Field(None, description="Metadados extraídos de um documento não classificado"),
    ]


class REAPResponseDTO(BaseModel):
    anos_verificados: Annotated[
        list[int],
        Field(..., description="Lista de anos de REAP verificados no documento"),
    ]
    anos_faltando: Annotated[
        list[int],
        Field(..., description="Lista de anos de REAP que estão faltando no documento"),
    ]
    completo: Optional[bool] = Field(
        None,
        description="Indica se o pescador possui REAPs para todos os anos obrigatórios (2021-2024)",
    )


class RegistrationDocumentResponseDTO(BaseModel):
    nome: Annotated[
        Optional[str],
        Field(None, description="Nome completo do titular do documento de registro"),
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            None,
            description="Número do CPF do titular do documento de registro no formato ###.###.###-##",
        ),
    ]
    documento_existe: Annotated[
        bool,
        Field(..., description="Indica se o documento de registro foi encontrado"),
    ]


class DocumentClassificationResponseDTO(BaseModel):
    classification: Annotated[
        DocumentClassification, Field(..., description="Classificação do documento")
    ]


class PowerOfAttorneyGrant(BaseModel):
    nome: Annotated[
        Optional[str],
        Field(..., description="Nome completo do outorgante da procuração"),
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            ...,
            description="Número do CPF do outorgante no formato ###.###.###-##",
        ),
    ]
    profissao: Annotated[
        Optional[str], Field(..., description="Profissão do outorgante da procuração")
    ]
    estado_civil: Annotated[
        Optional[str],
        Field(..., description="Estado civil do outorgante da procuração"),
    ]
    endereco: Annotated[
        _Endereco,
        Field(..., description="Endereço completo do outorgante da procuração"),
    ]
    telefone: Annotated[
        Optional[str],
        Field(None, description="Número de telefone do outorgante da procuração"),
    ]


class PowerOfAttorneyGranted(BaseModel):
    nome: Annotated[
        Optional[str],
        Field(..., description="Nome completo do outorgado da procuração"),
    ]
    cpf: Annotated[
        Optional[str],
        Field(
            ...,
            description="Número do CPF do outorgado no formato ###.###.###-##",
        ),
    ]
    numero_oab: Annotated[
        Optional[str],
        Field(None, description="Número da OAB do outorgado da procuração"),
    ]


class PowerOfAttorneyResponseDTO(BaseModel):
    ortogante: Annotated[
        PowerOfAttorneyGrant,
        Field(..., description="Dados do outorgante da procuração"),
    ]
    outorgados: Annotated[
        List[Optional[PowerOfAttorneyGranted]],
        Field(..., description="Dados do outorgado da procuração"),
    ]
