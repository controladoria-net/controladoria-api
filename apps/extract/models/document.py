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
        O CNIS (Cadastro Nacional de Informações Sociais) é um documento emitido pelo INSS que reúne o histórico laboral e previdenciário de uma pessoa,
        incluindo vínculos empregatícios, contribuições, períodos de atividade e dados cadastrais.

        ⚖️ Contexto Jurídico:
        No caso de pescadores profissionais, o CNIS é utilizado para comprovar o exercício da atividade pesqueira e a condição de Segurado Especial,
        requisito essencial para a concessão do Seguro-Defeso.

        A IA deve verificar:
        - Se o documento contém vínculo ativo de "Segurado Especial" ou contribuições compatíveis com a pesca artesanal;
        - Se o período aquisitivo do defeso (12 meses anteriores à abertura do defeso) está completo;
        - Se há outros vínculos empregatícios ou benefícios incompatíveis com o Seguro-Defeso (ex: empregos urbanos, aposentadoria, etc.);
        - Datas de início e fim da atividade pesqueira registradas no CNIS.

        Campos esperados no CNIS:
        - Nome completo do pescador;
        - CPF;
        - NIS/PIS/PASEP;
        - Data de nascimento;
        - Nome da mãe (se constar);
        - Categoria do segurado (ex: Empregado, Contribuinte Individual, Segurado Especial);
        - Data de início e fim da atividade de Segurado Especial;
        - Situação do vínculo (ativo ou encerrado);
        - Indicação se o período aquisitivo do defeso está completo (True/False);
        - Outros vínculos e remunerações, se existirem;
        - Órgão emissor: normalmente “INSS”.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "nis": types.Schema(
                type=GType.STRING,
                description="Número de inscrição social (NIS, PIS ou PASEP)."
            ),
            "data_nascimento": data_nascimento,
            "mae": types.Schema(
                type=GType.STRING,
                description="Nome da mãe do pescador."
            ),
            "categoria": types.Schema(
                type=GType.STRING,
                description="Categoria do segurado (ex: Segurado Especial, Contribuinte Individual, etc.)."
            ),
            "data_inicio_atividade": types.Schema(
                type=GType.STRING,
                format="date",
                description="Data de início da atividade de Segurado Especial."
            ),
            "data_fim_atividade": types.Schema(
                type=GType.STRING,
                format="date",
                description="Data de fim da atividade de Segurado Especial (se houver).",
                nullable=True
            ),
            "periodo_aquisitivo_defeso": types.Schema(
                type=GType.BOOLEAN,
                description=(
                    "Indica se o pescador possui atividade pesqueira ou contribuições nos 12 meses "
                    "anteriores ao início do período de defeso (True = cumpre, False = não cumpre)."
                )
            ),
            "outros_vinculos": types.Schema(
                type=GType.ARRAY,
                description="Lista de vínculos empregatícios não relacionados à pesca.",
                items=types.Schema(
                    type=GType.OBJECT,
                    properties={
                        "cnpj": types.Schema(type=GType.STRING, description="CNPJ do empregador."),
                        "razao_social": types.Schema(type=GType.STRING, description="Razão social do empregador."),
                        "data_admissao": types.Schema(type=GType.STRING, format="date", description="Data de admissão."),
                        "data_demissao": types.Schema(type=GType.STRING, format="date", description="Data de demissão."),
                        "categoria": types.Schema(type=GType.STRING, description="Categoria do vínculo."),
                        "situacao": types.Schema(
                            type=GType.STRING,
                            description="Situação do vínculo.",
                            enum=["ativo", "encerrado", "suspenso", "outros"],
                        ),
                    },
                    required=["cnpj", "razao_social", "data_admissao", "categoria", "situacao"],
                ),
            ),
            "orgao_emissor": types.Schema(
                type=GType.STRING,
                description="Órgão emissor do documento, normalmente 'INSS'."
            ),
        },
        required=[
            "nome",
            "cpf",
            "nis",
            "categoria",
            "data_inicio_atividade",
            "periodo_aquisitivo_defeso",
            "orgao_emissor",
        ],
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
            - Data do primeiro registro - “Data 1º RGP” indica o primeiro registro do pescador no sistema do Ministério da Pesca.
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
            "data_primeiro_registro": types.Schema(type=GType.STRING, format="date", description="Data referente ao primeiro registro."),
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
    sigla="COMPROVANTE_RESIDENCIA",
    instruction="""
        O Comprovante de Residência é um documento que atesta o endereço residencial de uma pessoa.
        Pode estar em formato PDF texto ou PDF imagem (escaneado/fotografado).

        Caso o documento esteja em formato de imagem, utilize OCR visual (interpretação de texto em imagem)
        para identificar os dados impressos.

        Campos esperados:
        - Nome do titular do comprovante;
        - Endereço completo (rua, número, bairro, cidade, estado, CEP);
        - Data de emissão (ou vencimento, se for conta de consumo);
        - Entidade emissora (companhia de luz, água, telefone etc.);
        - Tipo de documento (conta de energia, conta de água, etc.).
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "endereco": endereco,
            "data_emissao": data_emissao,
            "entidade_emissora": types.Schema(type=GType.STRING, description="Nome da entidade emissora, ex: Equatorial Energia."),
            "tipo_documento": types.Schema(type=GType.STRING, description="Tipo do comprovante, ex: conta de luz, água, telefone."),
        },
        required=["nome", "endereco", "data_emissao", "entidade_emissora"],
    ),
)


TERMO_REPRESENTACAO = Descriptor(
    name="Termo de Representação e Procuração",
    sigla="TERMO_REPRESENTACAO",
    instruction="""
        O Termo de Representação e Procuração é o documento pelo qual o pescador (outorgante)
        autoriza advogados a representá-lo em processos administrativos e judiciais.

        O documento pode chegar em dois arquivos separados (ex.: frente e verso). Analise o conjunto completo
        para verificar as informações antes de responder.

        O documento deve conter:
        - Identificação clara do pescador (nome completo);
        - Nome(s) do(s) advogado(s) responsável(is) pela representação;
        - Data de emissão ou validade;
        - Assinatura do pescador.

        ⚖️ Regras específicas obrigatórias:
        - O advogado **Rhycleyson Campos Paiva Martins** deve constar obrigatoriamente;
        - Se o nome **Carlos Magno Martins Cavaignac** constar, inclua-o na lista normalmente;
        - Caso o advogado obrigatório não apareça, retorne mesmo assim os dados extraídos,
          mas registre `advogado_obrigatorio_presente = false`;
        - Verifique se o documento está assinado pelo pescador (assinatura manuscrita ou digital identificável).

        ⚠️ Atenção:
        - Utilize OCR caso seja um PDF escaneado ou fotos;
        - Retorne somente o que está explícito nos arquivos analisados;
        - Não invente dados.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome_pescador": nome,
            "advogados": types.Schema(
                type=GType.ARRAY,
                description="Lista dos nomes dos advogados encontrados no termo.",
                items=types.Schema(
                    type=GType.STRING,
                    description="Nome do advogado mencionado no documento."
                ),
            ),
            "advogado_obrigatorio_presente": types.Schema(
                type=GType.BOOLEAN,
                description="True se 'Rhycleyson Campos Paiva Martins' estiver presente na lista de advogados."
            ),
            "assinatura_pescador": types.Schema(
                type=GType.BOOLEAN,
                description="True se houver assinatura do pescador no documento (digital ou manuscrita).",
            ),
            "data_emissao": data_emissao,
            "validade": types.Schema(
                type=GType.STRING,
                format="date",
                description="Data de validade do termo, se constar no documento.",
                nullable=True,
            ),
            "orgao_emissor": types.Schema(
                type=GType.STRING,
                description="Nome do escritório, entidade ou advogado responsável pela emissão.",
                nullable=True,
            ),
        },
        required=[
            "nome_pescador",
            "advogados",
            "advogado_obrigatorio_presente",
            "assinatura_pescador",
        ],
    ),
)

GPS = Descriptor(
    name="Guia da Previdência Social (GPS)",
    sigla="GPS",
    instruction="""
        A Guia da Previdência Social (GPS) é o comprovante de recolhimento da contribuição previdenciária individual ou empresarial. 
        Para o pescador, serve para comprovar recolhimento ao INSS no período de atividade pesqueira.

        Campos esperados no documento:
        - Nome completo do contribuinte (pescador);
        - CPF;
        - Código de pagamento (normalmente 1910, 2003, 2100 ou similar);
        - Competência (mês/ano de referência do pagamento);
        - Valor pago;
        - Data de pagamento;
        - Banco recebedor;
        - Identificação “GPS” no título do documento.
        
        ⚠️ Regras adicionais:
        - Verificar o “período de apuração” indicado no documento.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "codigo_pagamento": types.Schema(type=GType.STRING, description="Código de pagamento da GPS."),
            "competencia": types.Schema(type=GType.STRING, description="Mês/ano de referência da contribuição (formato MM/YYYY)."),
            "valor_pago": types.Schema(type=GType.NUMBER, description="Valor total pago conforme documento."),
            "data_pagamento": data_emissao,
            "banco": types.Schema(type=GType.STRING, description="Banco recebedor."),
            "periodo_apuracao": types.Schema(type=GType.STRING, description="Período de apuração do recolhimento."),
        },
        required=["nome", "cpf", "competencia", "valor_pago", "data_pagamento"],
    ),
)

BIOMETRIA = Descriptor(
    name="Comprovante de Biometria",
    sigla="BIOMETRIA",
    instruction="""
        O comprovante de biometria é uma captura (print ou PDF) emitida pela Justiça Eleitoral confirmando o cadastro biométrico do eleitor.

        Campos esperados no documento:
        - Nome completo do eleitor(a);
        - CPF (se disponível);
        - Número do título de eleitor;
        - Município e estado de cadastro;
        - Frase “ELEITOR/ELEITORA COM BIOMETRIA COLETADA” ou equivalente;
        - Data de emissão (caso conste).
        
        ⚠️ Regra obrigatória:
        - O campo 'biometria_coletada' deve ser verdadeiro apenas se o documento contiver a expressão acima.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "titulo_eleitor": types.Schema(type=GType.STRING, description="Número do título de eleitor."),
            "municipio": types.Schema(type=GType.STRING, description="Município do cadastro biométrico."),
            "estado": types.Schema(type=GType.STRING, description="UF do cadastro biométrico."),
            "biometria_coletada": types.Schema(
                type=GType.BOOLEAN,
                description="Verdadeiro se constar a frase 'ELEITOR/ELEITORA COM BIOMETRIA COLETADA'.",
            ),
            "data_emissao": data_emissao,
        },
        required=["nome", "titulo_eleitor", "biometria_coletada"],
    ),
)

REAP = Descriptor(
    name="Relatório de Exercício da Atividade Pesqueira (REAP)",
    sigla="REAP",
    instruction="""
        O Relatório de Exercício da Atividade Pesqueira (REAP) é um documento obrigatório para comprovar
        o exercício da atividade pesqueira em cada ano civil.

        ⚙️ Finalidade:
        Verificar se todos os REAPs referentes aos anos de 2021, 2022, 2023 e 2024 estão disponíveis
        na pasta de documentos do pescador.

        ⚠️ Regras obrigatórias:
        - Confirme a existência dos arquivos REAP_2021, REAP_2022, REAP_2023 e REAP_2024 (ou equivalentes);
        - Se faltar algum ano, liste quais não foram encontrados;
        - Caso todos estejam presentes, marque o campo “completo” como verdadeiro.

        O documento pode estar em formato PDF ou imagem, e deve conter identificação do pescador e assinatura,
        mas essa verificação não é obrigatória neste estágio.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "anos_verificados": types.Schema(
                type=GType.ARRAY,
                description="Lista dos anos encontrados (ex: [2021, 2022, 2023, 2024]).",
                items=types.Schema(type=GType.INTEGER),
            ),
            "anos_faltando": types.Schema(
                type=GType.ARRAY,
                description="Lista dos anos ausentes (ex: [2022, 2023]).",
                items=types.Schema(type=GType.INTEGER),
            ),
            "completo": types.Schema(
                type=GType.BOOLEAN,
                description="True se todos os REAPs de 2021 a 2024 estiverem presentes.",
            ),
        },
        required=["anos_verificados", "completo"],
    ),
)


DOCUMENTO_IDENTIDADE = Descriptor(
    name="Documento de Identidade",
    sigla="DOCUMENTO_IDENTIDADE",
    instruction="""
        Confirme se existe algum documento de identidade válido (RG, CNH, carteira profissional) no conteúdo analisado.

        Campos esperados no documento:
        - Nome completo da pessoa identificada;
        - CPF, se constar;
        - Informação se o documento de identidade foi encontrado.

        Caso nenhum documento de identidade válido seja identificado, retorne os campos vazios e marque `documento_existe` como falso.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "documento_existe": types.Schema(
                type=GType.BOOLEAN,
                description="True quando houver um documento de identidade válido identificado.",
            ),
        },
        required=["documento_existe"],
    ),
)





DOCUMENTO_IDENTIDADE_RG = Descriptor(
    name="Carteira de Identidade (RG)",
    sigla="DOCUMENTO_IDENTIDADE_RG",
    instruction="""
        Analise o RG enviado e confirme se se trata de um documento válido.

        Regras obrigatórias:
        - O documento deve apresentar o CPF do titular. Marque `cpf_encontrado` como false quando ele não aparecer;
        - Verifique se o RG corresponde ao modelo novo (presença de QR Code e CPF impresso). Se não identificar esses elementos, marque como false;
        - Caso não seja possível confirmar a existência de um RG, retorne `documento_existe` como false.
    """,
    response_mime_type="application/json",
    response_schema=types.Schema(
        type=GType.OBJECT,
        properties={
            "nome": nome,
            "cpf": cpf,
            "documento_existe": types.Schema(
                type=GType.BOOLEAN,
                description="True quando houver um RG legível no conteúdo analisado.",
            ),
            "cpf_encontrado": types.Schema(
                type=GType.BOOLEAN,
                description="True se o CPF do titular estiver visível no RG.",
            ),
            "documento_modelo_novo": types.Schema(
                type=GType.BOOLEAN,
                description="True se o RG for do modelo novo (com QR Code e CPF impresso).",
            ),
        },
        required=[
            "documento_existe",
            "cpf_encontrado",
            "documento_modelo_novo",
        ],
    ),
)


type Type = Literal[
    "CADASTRO_NACIONAL_INFORMACAO_SOCIAL",
    "CADASTRO_ATIVIDADE_ECONOMICA_PESSOA_FISICA",
    "COMPROVANTE_RESIDENCIA",
    "REGISTRO_GERAL_PESCA",
    "TERMO_REPRESENTACAO",
    "GPS",
    "BIOMETRIA",
    "RELATORIO_ATIVIDADE_PESQUEIRA",
    "DOCUMENTO_IDENTIDADE",
    "DOCUMENTO_IDENTIDADE_RG",
]

REGISTRY: dict[Type, Descriptor] = {
    "CADASTRO_NACIONAL_INFORMACAO_SOCIAL": CNIS,
    "CADASTRO_ATIVIDADE_ECONOMICA_PESSOA_FISICA": CAEPF,
    "COMPROVANTE_RESIDENCIA": COMPROVANTE_RESIDENCIA,
    "REGISTRO_GERAL_PESCA": RGP,
    "TERMO_REPRESENTACAO": TERMO_REPRESENTACAO,
    "GPS": GPS,
    "BIOMETRIA": BIOMETRIA,
    "RELATORIO_ATIVIDADE_PESQUEIRA": REAP,
    "DOCUMENTO_IDENTIDADE": DOCUMENTO_IDENTIDADE,
    "DOCUMENTO_IDENTIDADE_RG": DOCUMENTO_IDENTIDADE_RG,
}
