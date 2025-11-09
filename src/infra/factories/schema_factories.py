from infra.http.dto.extractor_dto import (
    CNISMetadataResponseDTO,
RGPMetadataResponseDTO,
CAEPFMetadataResponseDTO,
ComprovanteResidenciaMetadataResponseDTO,
TermoRepresentacaoMetadataResponseDTO,
GPSMetadataResponseDTO,
BiometriaMetadataResponseDTO,
DeclaracaoFiliacaoMetadataResponseDTO,
OutroMetadataResponseDTO
)
from domain.entities.categorias import CategoriaDocumento
from collections import defaultdict
from pydantic import BaseModel


_SCHEMA_REGISTRY_LIST = (
    CNISMetadataResponseDTO,
    RGPMetadataResponseDTO,
    CAEPFMetadataResponseDTO,
    ComprovanteResidenciaMetadataResponseDTO,
    TermoRepresentacaoMetadataResponseDTO,
    GPSMetadataResponseDTO,
    BiometriaMetadataResponseDTO,
    DeclaracaoFiliacaoMetadataResponseDTO,
    OutroMetadataResponseDTO,
)

_DOCUMENT_METADATA_SCHEMA_REGISTRY: dict[CategoriaDocumento | str, BaseModel] = defaultdict(lambda: OutroMetadataResponseDTO)
_DOCUMENT_METADATA_SCHEMA_REGISTRY.update(
    {
        CategoriaDocumento.CNIS: CNISMetadataResponseDTO,
        CategoriaDocumento.CERTIFICADO_DE_REGULARIDADE: RGPMetadataResponseDTO,
        CategoriaDocumento.CAEPF: CAEPFMetadataResponseDTO,
        CategoriaDocumento.DECLARACAO_DE_RESIDENCIA: ComprovanteResidenciaMetadataResponseDTO,
        CategoriaDocumento.TERMO_DE_REPRESENTACAO: TermoRepresentacaoMetadataResponseDTO,
        CategoriaDocumento.GPS_E_COMPROVANTE: GPSMetadataResponseDTO,
        CategoriaDocumento.BIOMETRIA: BiometriaMetadataResponseDTO,
        CategoriaDocumento.DECLARACAO_DE_FILIACAO: DeclaracaoFiliacaoMetadataResponseDTO,
        CategoriaDocumento.OUTRO: OutroMetadataResponseDTO,
    }
)

def create_document_metadata_extractor_by_categoria_use_case(categoria: CategoriaDocumento | str) -> BaseModel:
    return _DOCUMENT_METADATA_SCHEMA_REGISTRY[categoria]

def create_document_metadata_extractor_by_schema_use_case(schema_name: str) -> BaseModel:
    for schema in _SCHEMA_REGISTRY_LIST:
        if schema.__name__ == schema_name:
            return schema
    return OutroMetadataResponseDTO