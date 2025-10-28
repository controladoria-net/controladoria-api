from pydantic import BaseModel, ConfigDict
from google.genai import types
from google.genai.types import Type as GType
from typing import Optional
from textwrap import dedent
from typing import Literal


class Descriptor(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    sigla: Optional[str] = None
    instruction: str
    response_mime_type: Optional[str] = None
    response_schema: Optional[types.SchemaUnion] = None

    @property
    def system_instruction(self) -> str:
        return dedent(
            f"""
            ⚠️ Regras Gerais:
            - Responda apenas com JSON válido;
            - Se a informação não aparecer, não a inclua;
            - Utilize datas no formato YYYY-MM-DD;
            - Os documentos podem estar em formato PDF ou imagem (JPG/PNG);
            - Sempre identifique o tipo de documento com base nos termos mais evidentes no conteúdo;
            - Se não for possível identificar o documento, retorne um JSON vazio: `{{}}`;

            📜 Contexto
            {self.instruction}
        """
        )


nome = types.Schema(type=GType.STRING, description="Nome completo da pessoa referida no documento.")
cpf = types.Schema(type=GType.STRING, description="Número do CPF da pessoa referida no documento, no formato 000.000.000-00.", nullable=True)
data_nascimento = types.Schema(
    type=GType.STRING,
    format="date",
    description="Data de nascimento da pessoa referida no documento formato YYYY-MM-DD.",
    nullable=True,
)
data_emissao = types.Schema(
    type=GType.STRING,
    format="date",
    description="Data de emissão do documento, deve ser explícita no documento formato YYYY-MM-DD.",
    nullable=True,
)
endereco = types.Schema(
    type=GType.OBJECT,
    description="Endereço completo referente ao documento, ex.: residência, local de atividade, etc.",
    properties={
        "rua": types.Schema(type=GType.STRING, description="Nome da rua."),
        "numero": types.Schema(type=GType.STRING, description="Número da residência.", nullable=True),
        "complemento": types.Schema(type=GType.STRING, description="Complemento do endereço.", nullable=True),
        "bairro": types.Schema(type=GType.STRING, description="Bairro."),
        "cidade": types.Schema(type=GType.STRING, description="Cidade, município, localidade."),
        "estado": types.Schema(
            type=GType.STRING,
            description="Estado, sigla de duas letras. Caso esteja presente o nome completo, converta para sigla.",
        ),
        "cep": types.Schema(type=GType.STRING, description="CEP no formato 00000-000.", nullable=True),
    },
    required=["rua", "numero", "bairro", "cidade", "estado", "cep"],
)
CNIS = Descriptor(
    name="Cadastro Nacional de Informações Sociais",
    sigla="CNIS",
    instruction="""
        O CNIS (Cadastro Nacional de Informações Sociais) é um documento emitido pelo INSS / Ministério da Previdência Social que reúne o histórico laboral e previdenciário de uma pessoa, incluindo vínculos empregatícios, contribuições como autônomo, períodos de atividade e dados cadastrais.

        Ele é utilizado em solicitações de aposentadoria, benefícios previdenciários, seguro-desemprego e validação de vínculos e contribuições.

        O documento pode estar em PDF ou imagem (JPEG, PNG), e contém tabelas e seções textuais com informações de identificação e histórico.

        Campos esperados no CNIS:
        - Nome completo do trabalhador;
        - Número do CPF;
        - Número de inscrição social (NIS, PIS ou PASEP);
        - Data de nascimento;
        - Nome da mãe (se constar);
        - Órgão emissor: Normalmente “INSS” ou “Ministério da Previdência Social”;
        - Lista de vínculos empregatícios;


        A lista de vínculos empregatícios geralmente inclui:
        - CNPJ do empregador;
        - Razão social;
        - Data de admissão;
        - Data de demissão;
        - Categoria do trabalhador (ex: empregado, contribuinte individual, servidor público etc.);
        - Remuneração média (quando disponível);
        - Situação do vínculo (ativo, encerrado, etc.);
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "nis": types.Schema(type=GType.STRING, description="Número de inscrição social (NIS, PIS ou PASEP)."),
            "data_nascimento": data_nascimento,
            "mae": types.Schema(type=GType.STRING, description="Nome da mãe do trabalhador."),
            "ativo": types.Schema(
                type=GType.BOOLEAN,
                description="Indica se o trabalhador está ativo no CNIS. Se existir algum vínculo ativo, este campo deve ser true.",
            ),
            "vinculos": types.Schema(
                type=GType.ARRAY,
                description="Lista de vínculos empregatícios.",
                items=types.Schema(
                    type=GType.OBJECT,
                    properties={
                        "cnpj": types.Schema(type=GType.STRING, description="CNPJ do empregador no formato XX.XXX.XXX/XXXX-00."),
                        "razao_social": types.Schema(type=GType.STRING, description="Razão social do empregador."),
                        "data_admissao": types.Schema(type=GType.STRING, format="date", description="Data de admissão."),
                        "data_demissao": types.Schema(type=GType.STRING, format="date", description="Data de demissão."),
                        "categoria": types.Schema(type=GType.STRING, description="Categoria do trabalhador."),
                        "remuneracao_media": types.Schema(type=GType.NUMBER, description="Remuneração média."),
                        "situacao": types.Schema(
                            type=GType.STRING,
                            description="Situação do vínculo.",
                            enum=["ativo", "encerrado", "suspenso", "outros"],
                        ),
                    },
                    required=["cnpj", "razao_social", "data_admissao", "categoria", "situacao"],
                ),
            ),
        },
        required=["nome", "cpf", "nis", "data_nascimento", "vinculos"],
    ),
)

RGP = Descriptor(
    name="Registro Geral da Pesca",
    sigla="RGP",
    instruction="""
        O Certificado de Regularidade (Carteira RGP) é um documento emitido pelo Ministério da Pesca e Aquicultura (MPA) que comprova o registro ativo de um pescador no Registro Geral da Pesca (RGP). Ele serve como identificação oficial do pescador profissional e é obrigatório para acesso a benefícios como o Seguro-Desemprego do Pescador Artesanal (Seguro-Defeso).

        Este documento normalmente apresenta informações de identificação pessoal, profissional e administrativa do registro, podendo variar conforme o layout, mas deve conter os seguintes dados principais:

        Campos esperados no RGP:
            - Nome completo do pescador(a).
            - Número do CPF.
            - Número de registro no Registro Geral da Pesca.
            - Tipo de atividade exercida (ex: pescador artesanal, armador, aquicultor, etc.).
            - Categoria ou subcategoria dentro da modalidade, se houver.
            - Data de emissão do certificado.
            - Data de validade (caso conste no documento).
            - Situação do registro (ativo, suspenso, cancelado, etc.).
            - Município do domicílio do pescador.
            - Unidade Federativa (estado).
            - Órgão emissor do documento, normalmente “Ministério da Pesca e Aquicultura” ou equivalente.
        O documento pode estar em formato PDF ou imagem (JPEG, PNG), com logotipo oficial, brasão da República, e QR Code de autenticação.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "rgp": types.Schema(type=GType.INTEGER, description="Número de registro no Registro Geral da Pesca."),
            "atividade": types.Schema(type=GType.STRING, description="Tipo de atividade exercida."),
            "categoria": types.Schema(type=GType.STRING, description="Categoria ou subcategoria dentro da modalidade."),
            "data_emissao": data_emissao,
            "data_validade": types.Schema(type=GType.STRING, format="date", description="Data de validade do certificado."),
            "situacao": types.Schema(type=GType.STRING, description="Situação do registro.", enum=["ativo", "suspenso", "cancelado", "outros"]),
            "endereco": endereco,
            "orgao_emissor": types.Schema(type=GType.STRING, description="Órgão emissor do documento."),
        },
        required=["nome", "cpf", "rgp", "atividade", "data_emissao", "situacao", "endereco", "orgao_emissor"],
    ),
)

CAEPF = Descriptor(
    name="Cadastro de Atividade Econômica da Pessoa Física",
    sigla="CAEPF",
    instruction="""
        O CAEPF (Cadastro de Atividade Econômica da Pessoa Física) é um registro administrado pela Receita Federal do Brasil que identifica as atividades econômicas exercidas por pessoas físicas, como produtores rurais, profissionais autônomos, empregadores domésticos e contribuintes individuais.

        O documento (comprovante ou certificado de inscrição) contém informações cadastrais da pessoa física e da atividade registrada. Ele é utilizado para fins fiscais, previdenciários e trabalhistas, e pode ser apresentado em PDF ou imagem (JPEG, PNG).

        Campos esperados no CAEPF:
        - Nome completo da pessoa física titular do cadastro.
        - CPF do titular.
        - Número de inscrição no CAEPF.
        - Data de abertura ou inscrição.
        - Situação atual do cadastro (ativa, suspensa, cancelada, etc.).
        - Descrição da atividade econômica principal.
        - Código CNAE da atividade principal.
        - Endereço completo do local de atividade.
        - Município.
        - Unidade Federativa (estado).
        - Órgão emissor, geralmente “Receita Federal do Brasil”.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "caepf": types.Schema(type=GType.INTEGER, description="Número de inscrição no CAEPF."),
            "data_inscricao": types.Schema(type=GType.STRING, format="date", description="Data de abertura ou inscrição."),
            "situacao": types.Schema(
                type=GType.STRING,
                description="Situação atual do cadastro.",
                enum=["ativa", "suspensa", "cancelada", "outros"],
            ),
            "atividade_principal": types.Schema(type=GType.STRING, description="Descrição da atividade econômica principal."),
            "codigo_cnae": types.Schema(type=GType.STRING, description="Código CNAE da atividade principal."),
            "endereco": endereco,
            "orgao_emissor": types.Schema(type=GType.STRING, description="Órgão emissor do documento."),
        },
        required=["nome", "cpf", "caepf", "data_inscricao", "situacao", "atividade_principal", "codigo_cnae", "endereco", "orgao_emissor"],
    ),
)

COMPROVANTE_RESIDENCIA = Descriptor(
    name="Comprovante de Residência",
    instruction="""
        O Comprovante de Residência é um documento que atesta o endereço residencial de uma pessoa. Ele pode ser emitido por diversas entidades, como companhias de serviços públicos, instituições financeiras, órgãos governamentais, entre outros.

        O documento pode estar em formato PDF ou imagem (JPEG, PNG), e geralmente contém informações como nome do titular, endereço completo, data de emissão e o nome da entidade emissora.

        Campos esperados no Comprovante de Residência:
        - Nome completo do titular do comprovante.
        - Endereço completo (rua, número, complemento, bairro, cidade, estado,
            CEP).
        - Data de emissão do documento.
        - Nome da entidade emissora (ex: companhia de água, luz, banco, etc.).
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "endereco": endereco,
            "data_emissao": types.Schema(type=GType.STRING, format="date", description="Data de emissão do documento."),
            "tipo_documento": types.Schema(type=GType.STRING, description="Tipo de documento comprovante de residência."),
            "entidade_emissora": types.Schema(type=GType.STRING, description="Nome da entidade emissora"),
        },
        required=["nome", "cpf", "endereco", "data_emissao", "entidade_emissora"],
    ),
)

type Type = Literal[
    "CADASTRO_NACIONAL_INFORMACAO_SOCIAL",
    "CADASTRO_ATIVIDADE_ECONOMICA_PESSOA_FISICA",
    "COMPROVANTE_RESIDENCIA",
    "REGISTRO_GERAL_PESCA",
]

REGISTRY: dict[Type, Descriptor] = {
    "CADASTRO_NACIONAL_INFORMACAO_SOCIAL": CNIS,
    "CADASTRO_ATIVIDADE_ECONOMICA_PESSOA_FISICA": CAEPF,
    "COMPROVANTE_RESIDENCIA": COMPROVANTE_RESIDENCIA,
    "REGISTRO_GERAL_PESCA": RGP,
}
