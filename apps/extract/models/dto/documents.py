from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List, Mapping, Optional, Type as TypingType, Union, cast

from ..document import Type


@dataclass
class RGPDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    rgp: Optional[Union[int, str]] = None
    atividade: Optional[str] = None
    categoria: Optional[str] = None
    data_emissao: Optional[str] = None  # YYYY-MM-DD
    data_primeiro_registro: Optional[str] = None  # YYYY-MM-DD
    situacao: Optional[str] = None
    endereco: Optional[Dict[str, Any]] = None
    orgao_emissor: Optional[str] = None


@dataclass
class CAEPFDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    caepf: Optional[Union[int, str]] = None
    data_inscricao: Optional[str] = None  # YYYY-MM-DD
    situacao: Optional[str] = None
    atividade_principal: Optional[str] = None
    codigo_cnae: Optional[str] = None
    endereco: Optional[Dict[str, Any]] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    orgao_emissor: Optional[str] = None


@dataclass
class ComprovanteResidenciaDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    endereco: Optional[Dict[str, Any]] = None
    data_emissao: Optional[str] = None  # YYYY-MM-DD
    entidade_emissora: Optional[str] = None
    tipo_documento: Optional[str] = None


@dataclass
class CNISDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    nis: Optional[str] = None
    categoria: Optional[str] = None
    periodo_aquisitivo_defeso: Optional[bool] = None
    outros_vinculos: Optional[List[str]] = None
    beneficios_ativos: Optional[List[str]] = None
    data_inicio_atividade: Optional[str] = None  # YYYY-MM-DD
    data_fim_atividade: Optional[str] = None  # YYYY-MM-DD
    situacao_vinculo: Optional[str] = None


@dataclass
class TermoRepresentacaoDTO:
    nome_pescador: Optional[str] = None
    advogados: List[str] = field(default_factory=list)
    advogado_obrigatorio_presente: Optional[bool] = None
    assinatura_pescador: Optional[bool] = None
    data_emissao: Optional[str] = None  # YYYY-MM-DD
    validade: Optional[str] = None  # YYYY-MM-DD
    orgao_emissor: Optional[str] = None


@dataclass
class GPSDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    codigo_pagamento: Optional[str] = None
    competencia: Optional[str] = None  # MM/YYYY
    valor_pago: Optional[float] = None
    data_pagamento: Optional[str] = None  # YYYY-MM-DD
    banco: Optional[str] = None
    periodo_apuracao: Optional[str] = None


@dataclass
class BiometriaDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    titulo_eleitor: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    biometria_coletada: Optional[bool] = None
    data_emissao: Optional[str] = None  # YYYY-MM-DD


@dataclass
class DocumentoIdentidadeDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    documento_existe: Optional[bool] = None


@dataclass
class DocumentoIdentidadeRGDTO:
    nome: Optional[str] = None
    cpf: Optional[str] = None
    documento_existe: Optional[bool] = None
    cpf_encontrado: Optional[bool] = None
    documento_modelo_novo: Optional[bool] = None


@dataclass
class REAPDTO:
    anos_verificados: List[int] = field(default_factory=list)
    anos_faltando: List[int] = field(default_factory=list)
    completo: Optional[bool] = None


DTOType = TypingType[Any]

DTO_REGISTRY: Dict[str, DTOType] = {
    "REGISTRO_GERAL_PESCA": RGPDTO,
    "CADASTRO_ATIVIDADE_ECONOMICA_PESSOA_FISICA": CAEPFDTO,
    "COMPROVANTE_RESIDENCIA": ComprovanteResidenciaDTO,
    "CADASTRO_NACIONAL_INFORMACAO_SOCIAL": CNISDTO,
    "TERMO_REPRESENTACAO": TermoRepresentacaoDTO,
    "GPS": GPSDTO,
    "BIOMETRIA": BiometriaDTO,
    "RELATORIO_ATIVIDADE_PESQUEIRA": REAPDTO,
    "DOCUMENTO_IDENTIDADE": DocumentoIdentidadeDTO,
    "DOCUMENTO_IDENTIDADE_RG": DocumentoIdentidadeRGDTO,
}


def build_dto(doc_type: Union[Type, str], ai_response: Mapping[str, Any]):
    """
    Instantiates the DTO associated with ``doc_type`` using only the expected fields.
    Extra keys coming from the AI response are ignored.
    """
    doc_type_key = cast(str, doc_type)
    dto_class = DTO_REGISTRY.get(doc_type_key)
    if not dto_class:
        raise ValueError(f"Tipo de documento não suportado: {doc_type_key}")

    allowed_fields = {field_.name for field_ in fields(dto_class)}
    clean_data = {key: value for key, value in ai_response.items() if key in allowed_fields}
    return dto_class(**clean_data)


def dto_to_dict(dto: Any) -> Dict[str, Any]:
    """Helper to convert any DTO dataclass into a plain dictionary."""
    return asdict(dto)


__all__ = [
    "BiometriaDTO",
    "CAEPFDTO",
    "CNISDTO",
    "ComprovanteResidenciaDTO",
    "DTO_REGISTRY",
    "DocumentoIdentidadeDTO",
    "DocumentoIdentidadeRGDTO",
    "GPSDTO",
    "RGPDTO",
    "REAPDTO",
    "TermoRepresentacaoDTO",
    "build_dto",
    "dto_to_dict",
]
