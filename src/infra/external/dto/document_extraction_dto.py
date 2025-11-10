from pydantic import BaseModel, Field
from typing import Optional, Annotated, Literal
from datetime import date
from google.genai.types import Schema

# TODO: Converter todos os DTOs desse arquivo para Types.Schema do Gemini
# Conversão realizada abaixo via objetos Schema do Gemini.


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


class CNISMetadataResponseDTO(BaseModel):
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


class RGPMetadataResponseDTO(BaseModel):
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


class CAEPFMetadataResponseDTO(BaseModel):
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


class ComprovanteResidenciaMetadataResponseDTO(BaseModel):
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


class TermoRepresentacaoMetadataResponseDTO(BaseModel):
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


class GPSMetadataResponseDTO(BaseModel):
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


class BiometriaMetadataResponseDTO(BaseModel):
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
            examples=["REGULAR", "IRREGULAR"],
        ),
    ]


class DeclaracaoFiliacaoMetadataResponseDTO(BaseModel):
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


class OutroMetadataResponseDTO(BaseModel):
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
        Optional[dict[str, str]],
        Field(None, description="Outras informações relevantes extraídas do documento"),
    ]


class ExtratorMetadataResponseDTO(BaseModel):
    cnis: Annotated[
        Optional[CNISMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento CNIS"),
    ]
    rgp: Annotated[
        Optional[RGPMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento RGP"),
    ]
    caepf: Annotated[
        Optional[CAEPFMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento CAEPF"),
    ]
    comprovante_residencia: Annotated[
        Optional[ComprovanteResidenciaMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um comprovante de residência"),
    ]
    termo_representacao: Annotated[
        Optional[TermoRepresentacaoMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um termo de representação"),
    ]
    gps: Annotated[
        Optional[GPSMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento GPS"),
    ]
    biometria: Annotated[
        Optional[BiometriaMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento de biometria"),
    ]
    declaracao_filiacao: Annotated[
        Optional[DeclaracaoFiliacaoMetadataResponseDTO],
        Field(None, description="Metadados extraídos de uma declaração de filiação"),
    ]
    outro: Annotated[
        Optional[OutroMetadataResponseDTO],
        Field(None, description="Metadados extraídos de um documento não classificado"),
    ]


class REAPMetadataResponseDTO(BaseModel):
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

# =============================
# Esquemas Gemini (Types.Schema)
# =============================

# Esquemas auxiliares (aninhados)
EnderecoSchema = Schema(
    type="object",
    description="Endereço completo extraído do documento",
    properties={
        "cep": Schema(type="string", description="CEP do endereço", nullable=True),
        "logradouro": Schema(
            type="string",
            description="Nome da rua/avenida do endereço",
        ),
        "numero": Schema(
            type="string",
            description="Número do endereço",
            nullable=True,
        ),
        "complemento": Schema(
            type="string",
            description="Complemento do endereço",
            nullable=True,
        ),
        "bairro": Schema(type="string", description="Bairro"),
        "municipio": Schema(type="string", description="Município"),
        "uf": Schema(
            type="string",
            description="UF do estado (ex.: SP, RJ)",
        ),
    },
)

VinculoCNISSchema = Schema(
    type="object",
    description="Vínculo empregatício do trabalhador no CNIS",
    properties={
        "cnpj": Schema(
            type="string",
            description="CNPJ da empresa vinculada"
        ),
        "razao_social": Schema(
            type="string",
            description="Razão social da empresa"
        ),
        "data_admissao": Schema(
            type="string",
            description="Data de admissão (YYYY-MM-DD)",
        ),
        "data_demissao": Schema(
            type="string",
            description="Data de demissão (YYYY-MM-DD)",
            nullable=True,
        ),
        "categoria": Schema(
            type="string",
            description="Categoria do trabalhador"
        ),
        "remuneracao_media": Schema(
            type="number",
            description="Remuneração média mensal",
            nullable=True,
        ),
        "situacao": Schema(
            type="string",
            description="Situação do vínculo",
            enum=["ATIVO", "INATIVO", "SUSPENSO", "OUTRO"],
        ),
    },
)

ComposicaoDocumentoGPSSchema = Schema(
    type="object",
    description="Composição de valores do documento GPS",
    properties={
        "codigo": Schema(type="string", description="Código da composição"),
        "denominacao": Schema(
            type="string", description="Denominação da composição"
        ),
        "principal": Schema(type="number", description="Valor principal"),
        "multa": Schema(type="number", description="Valor da multa"),
        "juros": Schema(type="number", description="Valor dos juros"),
        "total": Schema(type="number", description="Valor total"),
    },
)

RepresentanteLegalSchema = Schema(
    type="object",
    description="Dados do representante legal",
    properties={
        "nome": Schema(type="string", description="Nome do representante"),
        "orgao_emissor_oab": Schema(
            type="string",
            description="Órgão emissor da OAB",
            nullable=True,
        ),
        "numero_oab": Schema(
            type="string",
            description="Número da OAB",
            nullable=True,
        ),
        "cpf": Schema(
            type="string",
            description="CPF do representante",
            nullable=True,
        ),
    },
)

# Esquemas principais (um por tipo de documento)
CNISMetadataResponseShema = Schema(
    type="object",
    description="Metadados extraídos do documento CNIS",
    properties={
        "nome": Schema(type="string", description="Nome do trabalhador"),
        "cpf": Schema(type="string", description="CPF do trabalhador"),
        "data_nascimento": Schema(
            type="string", description="Data de nascimento (YYYY-MM-DD)"
        ),
        "inscricao": Schema(type="string", description="Número de inscrição no CNIS"),
        "tipo_inscricao": Schema(
            type="string",
            description="Tipo de inscrição (NIS/PIS/PASEP)",
            enum=["NIS", "PIS", "PASEP"],
        ),
        "mae": Schema(
            type="string",
            description="Nome da mãe",
            nullable=True,
        ),
        "ativo": Schema(type="boolean", description="Se possui vínculo vigente"),
        "vinculos": Schema(
            type="array",
            description="Lista de vínculos",
            items=VinculoCNISSchema,
        ),
    },
)

RGPMetadataResponseSchema = Schema(
    type="object",
    description="Metadados extraídos do documento RGP",
    properties={
        "tipo_licenca": Schema(
            type="string",
            description="Tipo de licença do RGP",
        ),
        "nome": Schema(type="string", description="Nome do titular"),
        "cpf": Schema(
            type="string",
            description="CPF do titular",
            nullable=True,
        ),
        "rgp": Schema(type="string", description="Número do RGP"),
        "categoria": Schema(
            type="string", description="Categoria da atividade pesqueira"
        ),
        "data_nascimento": Schema(
            type="string", description="Data de nascimento (YYYY-MM-DD)"
        ),
        "data_emissao": Schema(
            type="string",
            description="Data de emissão (YYYY-MM-DD)",
            nullable=True,
        ),
        "data_validade": Schema(
            type="string",
            description="Data de validade (YYYY-MM-DD)",
            nullable=True,
        ),
        "orgao_emissor": Schema(
            type="string", description="Órgão emissor do RGP", nullable=True
        ),
        "filiacao": Schema(
            type="string", description="Filiação do titular", nullable=True
        ),
        "municipio_residencia": Schema(
            type="string",
            description="Município de residência",
            nullable=True,
        ),
    },
)

CAEPFMetadataResponseSchema = Schema(
    type="object",
    description="Metadados extraídos do documento CAEPF",
    properties={
        "nome": Schema(type="string", description="Nome do titular"),
        "cpf": Schema(type="string", description="CPF do titular"),
        "caepf": Schema(type="string", description="Número do CAEPF"),
        # Representado como string para simplificar a geração
        "cnae": Schema(
            type="string",
            description="Código(s) CNAE associado(s) ao CAEPF",
        ),
        "data_inscricao": Schema(
            type="string", description="Data de inscrição (YYYY-MM-DD)"
        ),
        "atividade_economica": Schema(
            type="string", description="Descrição da atividade econômica"
        ),
        "qualificacao": Schema(type="string", description="Qualificação do titular"),
        "data_inicio_atividade": Schema(
            type="string", description="Data de início (YYYY-MM-DD)"
        ),
        "situacao_cadastral": Schema(
            type="string",
            description="Situação cadastral",
            enum=[
                "ATIVO",
                "INATIVO",
                "SUSPENSO",
                "CANCELADO",
                "BAIXADO",
                "OUTRO",
            ],
        ),
        "endereco": EnderecoSchema,
    },
)

ComprovanteResidenciaMetadataResponseSchema = Schema(
    type="object",
    description="Metadados de Comprovante de Residência",
    properties={
        "nome": Schema(
            type="string",
            description="Nome completo do titular do comprovante",
        ),
        "cpf": Schema(
            type="string",
            description="CPF do titular",
            nullable=True,
        ),
        "endereco": EnderecoSchema,
        "data_emissao": Schema(
            type="string",
            description="Data de emissão (YYYY-MM-DD)",
            nullable=True,
        ),
        "tipo_documento": Schema(
            type="string",
            description="Tipo do documento (ex.: conta de luz)",
            nullable=True,
        ),
        "emissor": Schema(
            type="string",
            description="Entidade emissora",
            nullable=True,
        ),
    },
)

TermoRepresentacaoMetadataResponseSchema = Schema(
    type="object",
    description="Metadados do Termo de Representação",
    properties={
        "nome": Schema(type="string", description="Nome do titular"),
        "estado_civil": Schema(type="string", description="Estado civil"),
        "profissao": Schema(type="string", description="Profissão"),
        "rg": Schema(type="string", description="Número do RG"),
        "cpf": Schema(type="string", description="CPF do titular"),
        "endereco": EnderecoSchema,
        "telefone": Schema(
            type="string", description="Telefone do titular", nullable=True
        ),
        "email": Schema(
            type="string", description="E-mail do titular", nullable=True
        ),
        "contem_assinatura": Schema(
            type="boolean",
            description="Indica se o termo está assinado",
        ),
        "representante_legal": Schema(
            type="array",
            description="Lista de representantes legais",
            items=RepresentanteLegalSchema,
        ),
    },
)

GPSMetadataResponseSchema = Schema(
    type="object",
    description="Metadados do documento GPS",
    properties={
        "nome": Schema(type="string", description="Nome do contribuinte"),
        "cpf": Schema(type="string", description="CPF do contribuinte"),
        "competencia": Schema(
            type="string", description="Competência no formato MM/YYYY"
        ),
        "data_vencimento": Schema(
            type="string", description="Data de vencimento (YYYY-MM-DD)"
        ),
        "numero_documento": Schema(
            type="string", description="Número do documento da GPS"
        ),
        "observacoes": Schema(
            type="string",
            description="Observações adicionais",
            nullable=True,
        ),
        "valor_total": Schema(type="number", description="Valor total a pagar"),
        "composicao": Schema(
            type="array",
            description="Composição do documento",
            items=ComposicaoDocumentoGPSSchema,
        ),
        "comprovante_pagamento": Schema(
            type="boolean",
            description="Se há comprovante de pagamento anexado",
            nullable=True,
        ),
    },
)

BiometriaMetadataResponseSchema = Schema(
    type="object",
    description="Metadados do comprovante de biometria",
    properties={
        "nome": Schema(
            type="string",
            description="Nome do titular",
            nullable=True,
        ),
        "cpf": Schema(type="string", description="CPF do titular"),
        "titulo_eleitor": Schema(
            type="string", description="Número do título de eleitor"
        ),
        "municipio": Schema(
            type="string", description="Município do cadastro", nullable=True
        ),
        "estado": Schema(
            type="string", description="Estado do cadastro", nullable=True
        ),
        "data_emissao": Schema(
            type="string", description="Data de emissão (YYYY-MM-DD)", nullable=True
        ),
        "zona": Schema(type="string", description="Zona eleitoral", nullable=True),
        "secao": Schema(type="string", description="Seção eleitoral", nullable=True),
        "situacao": Schema(
            type="string",
            description="Situação da biometria (ex.: REGULAR/IRREGULAR)",
        ),
    },
)

DeclaracaoFiliacaoMetadataResponseSchema = Schema(
    type="object",
    description="Metadados da Declaração de Filiação",
    properties={
        "nome": Schema(type="string", description="Nome do titular"),
        "cpf": Schema(type="string", description="CPF do titular"),
        "endereco": EnderecoSchema,
        "nome_entidade": Schema(
            type="string", description="Nome da entidade de filiação"
        ),
        "cnpj_entidade": Schema(
            type="string", description="CNPJ da entidade", nullable=True
        ),
        "nome_representante": Schema(
            type="string", description="Nome do representante legal"
        ),
        "cpf_representante": Schema(
            type="string",
            description="CPF do representante legal",
            nullable=True,
        ),
        "endereco_entidade": EnderecoSchema,
        "municipio_emissao": Schema(
            type="string", description="Município de emissão"
        ),
        "delegacia_emissao": Schema(
            type="string", description="Delegacia de emissão", nullable=True
        ),
        "data_filiacao": Schema(
            type="string", description="Data de filiação (YYYY-MM-DD)"
        ),
        "data_emissao": Schema(
            type="string", description="Data de emissão (YYYY-MM-DD)"
        ),
    },
)

OutroMetadataResponseSchema = Schema(
    type="object",
    description="Metadados de documento não classificado",
    properties={
        "nome": Schema(
            type="string", description="Nome extraído", nullable=True
        ),
        "cpf": Schema(
            type="string",
            description="CPF extraído",
            nullable=True,
        ),
        "endereco": Schema(
            type="object",
            description="Endereço extraído, se houver",
            nullable=True,
            properties=EnderecoSchema.properties,  # reusa estrutura
        ),
        "orgao_emissor": Schema(
            type="string", description="Órgão emissor", nullable=True
        ),
        "data_emissao": Schema(
            type="string",
            description="Data de emissão (YYYY-MM-DD)",
            nullable=True,
        ),
        "tipo_documento": Schema(
            type="string", description="Tipo do documento", nullable=True
        ),
        "informacoes_adicionais": Schema(
            type="object",
            description="Mapa de informações adicionais",
            nullable=True,
            additional_properties=Schema(type="string"),
        ),
    },
)

ExtratorMetadataResponseSchema = Schema(
    type="object",
    description="Envelope com metadados por tipo de documento",
    properties={
        "cnis": Schema(type="object", nullable=True, properties=CNISMetadataResponseShema.properties),
        "rgp": Schema(type="object", nullable=True, properties=RGPMetadataResponseSchema.properties),
        "caepf": Schema(type="object", nullable=True, properties=CAEPFMetadataResponseSchema.properties),
        "comprovante_residencia": Schema(
            type="object",
            nullable=True,
            properties=ComprovanteResidenciaMetadataResponseSchema.properties,
        ),
        "termo_representacao": Schema(
            type="object",
            nullable=True,
            properties=TermoRepresentacaoMetadataResponseSchema.properties,
        ),
        "gps": Schema(type="object", nullable=True, properties=GPSMetadataResponseSchema.properties),
        "biometria": Schema(
            type="object",
            nullable=True,
            properties=BiometriaMetadataResponseSchema.properties,
        ),
        "declaracao_filiacao": Schema(
            type="object",
            nullable=True,
            properties=DeclaracaoFiliacaoMetadataResponseSchema.properties,
        ),
        "outro": Schema(
            type="object", nullable=True, properties=OutroMetadataResponseSchema.properties
        ),
    },
)

REAPMetadataResponseSchema = Schema(
    type="object",
    description="Metadados do REAP (anos verificados/faltando)",
    properties={
        "anos_verificados": Schema(
            type="array", description="Anos verificados", items=Schema(type="integer")
        ),
        "anos_faltando": Schema(
            type="array", description="Anos faltantes", items=Schema(type="integer")
        ),
        "completo": Schema(
            type="boolean",
            description="Se possui REAP para todos os anos obrigatórios",
            nullable=True,
        ),
    },
)

RegistrationDocumentResponseSchema = Schema(
    type="object",
    description="Verificação de existência de documento de identidade (CIN/CPF)",
    properties={
        "nome": Schema(type="string", description="Nome do titular", nullable=True),
        "cpf": Schema(type="string", description="CPF do titular", nullable=True),
        "documento_existente": Schema(
            type="boolean", description="Indica se o documento existe"
        ),
    },
)
