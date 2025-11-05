from typing import Dict, Optional, Tuple

from src.domain.core.logger import get_logger
from src.domain.entities.case import CNJNumber, LegalCase
from src.domain.gateway.legal_case_gateway import LegalCaseGateway

logger = get_logger(__name__)


COURT_CODE_MAP: Dict[Tuple[str, str], str] = {
    # --- Superior Courts (TR = 00) ---
    ("3", "00"): "stj",  # Superior Tribunal de Justiça
    ("5", "00"): "tst",  # Tribunal Superior do Trabalho
    ("6", "00"): "tse",  # Tribunal Superior Eleitoral
    ("7", "00"): "stm",  # Superior Tribunal Militar
    # --- Federal Courts (J = 4) ---
    ("4", "01"): "trf1",  # TRF da 1ª Região
    ("4", "02"): "trf2",  # TRF da 2ª Região
    ("4", "03"): "trf3",  # TRF da 3ª Região
    ("4", "04"): "trf4",  # TRF da 4ª Região
    ("4", "05"): "trf5",  # TRF da 5ª Região
    ("4", "06"): "trf6",  # TRF da 6ª Região
    # --- Labor Courts (J = 5) ---
    ("5", "01"): "trt1",
    ("5", "02"): "trt2",
    ("5", "03"): "trt3",
    ("5", "04"): "trt4",
    ("5", "05"): "trt5",
    ("5", "06"): "trt6",
    ("5", "07"): "trt7",
    ("5", "08"): "trt8",
    ("5", "09"): "trt9",
    ("5", "10"): "trt10",
    ("5", "11"): "trt11",
    ("5", "12"): "trt12",
    ("5", "13"): "trt13",
    ("5", "14"): "trt14",
    ("5", "15"): "trt15",
    ("5", "16"): "trt16",
    ("5", "17"): "trt17",
    ("5", "18"): "trt18",
    ("5", "19"): "trt19",
    ("5", "20"): "trt20",
    ("5", "21"): "trt21",
    ("5", "22"): "trt22",
    ("5", "23"): "trt23",
    ("5", "24"): "trt24",
    # --- State Courts (J = 8) ---
    ("8", "01"): "tjac",  # Acre
    ("8", "02"): "tjal",  # Alagoas
    ("8", "03"): "tjap",  # Amapá
    ("8", "04"): "tjam",  # Amazonas
    ("8", "05"): "tjba",  # Bahia
    ("8", "06"): "tjce",  # Ceará
    ("8", "07"): "tjdft",  # Distrito Federal e Territórios
    ("8", "08"): "tjes",  # Espírito Santo
    ("8", "09"): "tjgo",  # Goiás
    ("8", "10"): "tjma",  # Maranhão
    ("8", "11"): "tjmt",  # Mato Grosso
    ("8", "12"): "tjms",  # Mato Grosso do Sul
    ("8", "13"): "tjmg",  # Minas Gerais
    ("8", "14"): "tjpa",  # Pará
    ("8", "15"): "tjpb",  # Paraíba
    ("8", "16"): "tjpr",  # Paraná
    ("8", "17"): "tjpe",  # Pernambuco
    ("8", "18"): "tjpi",  # Piauí
    ("8", "19"): "tjrj",  # Rio de Janeiro
    ("8", "20"): "tjrn",  # Rio Grande do Norte
    ("8", "21"): "tjrs",  # Rio Grande do Sul
    ("8", "22"): "tjro",  # Rondônia
    ("8", "23"): "tjrr",  # Roraima
    ("8", "24"): "tjsc",  # Santa Catarina
    ("8", "25"): "tjsp",  # São Paulo
    ("8", "26"): "tjse",  # Sergipe
    ("8", "27"): "tjto",  # Tocantins
}


class FindLegalCaseUseCase:
    def __init__(self, gateway: LegalCaseGateway):
        self.gateway = gateway

    def execute(self, raw_case_number: str) -> Optional[LegalCase]:
        try:
            cnj_identifier = CNJNumber.from_raw(raw_case_number)

            judiciary_code = cnj_identifier.judiciary_branch_code
            court_code = cnj_identifier.court_code

            court_acronym = COURT_CODE_MAP.get((judiciary_code, court_code))

            if not court_acronym:
                logger.error(
                    "Combinação J='%s', TR='%s' não está mapeada para o CNJ '%s'.",
                    judiciary_code,
                    court_code,
                    cnj_identifier.number,
                )
                return None

            logger.info(
                "Tribunal identificado como %s. Consultando com o CNJ '%s'",
                court_acronym.upper(),
                cnj_identifier.number,
            )
            return self.gateway.find_case_by_number(
                case_number=cnj_identifier, court_acronym=court_acronym
            )

        except ValueError as e:
            logger.error(
                "Falha na validação do número '%s'. details: %s", raw_case_number, e
            )
            return None
        except Exception as e:
            logger.error("Ocorreu um erro inesperado: %s", e)
            return None
