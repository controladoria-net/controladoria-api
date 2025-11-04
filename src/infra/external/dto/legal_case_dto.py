from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ClasseDTO:
    nome: Optional[str] = None


@dataclass
class OrgaoJulgadorDTO:
    nome: Optional[str] = None


@dataclass
class AssuntoDTO:
    nome: Optional[str] = None


@dataclass
class MovimentoDTO:
    data_hora: Optional[str] = None
    nome: Optional[str] = None
    complementos_tabelados: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LegalCaseRawDTO:
    numero_processo: Optional[str] = None
    tribunal: Optional[str] = None
    classe: Optional[ClasseDTO] = None
    orgao_julgador: Optional[OrgaoJulgadorDTO] = None
    data_ajuizamento: Optional[str] = None
    grau: Optional[str] = None
    assuntos: List[AssuntoDTO] = field(default_factory=list)
    movimentos: List[MovimentoDTO] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LegalCaseRawDTO":
        classe_data = data.get("classe", {})
        classe_obj = ClasseDTO(nome=classe_data.get("nome")) if classe_data else None

        orgao_data = data.get("orgaoJulgador", {})
        orgao_obj = (
            OrgaoJulgadorDTO(nome=orgao_data.get("nome")) if orgao_data else None
        )

        assuntos_list = [
            AssuntoDTO(nome=a.get("nome"))
            for a in data.get("assuntos", [])
            if a and isinstance(a, dict)
        ]

        movimentos_list = [
            MovimentoDTO(
                data_hora=m.get("dataHora"),
                nome=m.get("nome"),
                complementos_tabelados=m.get("complementosTabelados", []),
            )
            for m in data.get("movimentos", [])
            if m and isinstance(m, dict)
        ]

        # 2. Constrói o DTO principal com os objetos seguros
        return cls(
            numero_processo=data.get("numeroProcesso"),
            tribunal=data.get("tribunal"),
            classe=classe_obj,
            orgao_julgador=orgao_obj,
            data_ajuizamento=data.get("dataAjuizamento"),
            grau=data.get("grau"),
            assuntos=assuntos_list,
            movimentos=movimentos_list,
        )
