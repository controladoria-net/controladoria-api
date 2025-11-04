from typing import Optional, List
from datetime import datetime

from src.domain.entities.case import CNJNumber, LegalCase, Movement
from src.infra.external.dto.legal_case_dto import LegalCaseRawDTO, MovimentoDTO


class LegalCaseMapper:
    @staticmethod
    def _map_case_number(raw_case_number: Optional[str]) -> Optional[str]:
        if not raw_case_number:
            return None

        case_number = raw_case_number.strip()
        if not case_number:
            return None

        if case_number.isdigit():
            try:
                return CNJNumber.from_raw(case_number).number
            except ValueError:
                return case_number

        try:
            return CNJNumber(number=case_number).number
        except ValueError:
            return case_number

    @staticmethod
    def _parse_datetime(date_string: Optional[str]) -> datetime:
        if not date_string:
            return datetime.min
        try:
            if date_string.endswith("Z"):
                date_string = date_string[:-1] + "+00:00"
            return datetime.fromisoformat(date_string)
        except (ValueError, TypeError):
            return datetime.min

    @staticmethod
    def _map_movements(movement_dtos: List[MovimentoDTO]) -> List[Movement]:
        domain_movements = []
        for dto in movement_dtos:
            description = dto.nome or ""
            for comp in dto.complementos_tabelados:
                if comp_name := comp.get("nome"):
                    description += f" - {comp_name}"
            domain_movements.append(
                Movement(
                    date=LegalCaseMapper._parse_datetime(dto.data_hora),
                    description=description.strip(),
                )
            )
        domain_movements.sort(key=lambda m: m.date)
        return domain_movements

    @staticmethod
    def from_dto_to_domain(dto: LegalCaseRawDTO) -> LegalCase:
        movements = LegalCaseMapper._map_movements(dto.movimentos)
        latest_update = (
            movements[-1].description
            if movements
            else "Nenhuma movimentação encontrada"
        )
        return LegalCase(
            case_number=LegalCaseMapper._map_case_number(dto.numero_processo),
            court=dto.tribunal or None,
            judging_body=(dto.orgao_julgador.nome if dto.orgao_julgador else None),
            procedural_class=dto.classe.nome if dto.classe else None,
            subject=dto.assuntos[0].nome if dto.assuntos else None,
            status=dto.grau or None,
            filing_date=LegalCaseMapper._parse_datetime(dto.data_ajuizamento),
            latest_update=latest_update,
            movement_history=movements if movements else None,
        )
