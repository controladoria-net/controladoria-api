import os
from typing import Dict, Optional
from dotenv import load_dotenv
import requests

from domain.gateway.legal_case_gateway import LegalCaseGateway
from domain.entities.case import LegalCase
from infra.external.dto.legal_case_dto import LegalCaseRawDTO
from infra.external.mapper.legal_case_mapper import LegalCaseMapper

load_dotenv()
DATAJUD_API_KEY = os.getenv("DATAJUD_API_KEY")
DATAJUD_URL = os.getenv("DATAJUD_URL")


class DataJudGateway(LegalCaseGateway):
    """
    Implementação do gateway que consulta a API DataJud do CNJ.
    """

    def __init__(self):
        self.api_key = DATAJUD_API_KEY
        self.base_url = DATAJUD_URL
        self.tribunal_acronyms = [
            "tst",
            "tse",
            "stj",
            "stm",
            "trf1",
            "trf2",
            "trf3",
            "trf4",
            "trf5",
            "trf6",
            "tjma",
            "trt1",
            "trt2",
            "trt3",
            "trt4",
            "trt5",
            "trt6",
            "trt7",
            "trt8",
            "trt9",
            "trt10",
            "trt11",
            "trt12",
            "trt13",
            "trt14",
            "trt15",
            "trt16",
            "trt17",
            "trt18",
            "trt19",
            "trt20",
            "trt21",
            "trt22",
            "trt23",
            "trt24",
        ]

    def _get_headers(self) -> Dict[str, str]:
        """Cria o cabeçalho padrão para as requisições."""
        return {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

    def find_case_by_number(self, case_number: str) -> Optional[LegalCase]:
        payload = {"query": {"match": {"numeroProcesso": case_number}}}
        headers = self._get_headers()
        for acronym in self.tribunal_acronyms:
            url = f"{self.base_url}/api_publica_{acronym}/_search"
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                response.raise_for_status()
                data = response.json()
                if hits := data.get("hits", {}).get("hits", []):
                    print(
                        f"-> Processo encontrado em {acronym.upper()}! Mapeando dados..."
                    )
                    dto = LegalCaseRawDTO.from_dict(hits[0]["_source"])
                    return LegalCaseMapper.from_dto_to_domain(dto)
            except requests.exceptions.RequestException as e:
                print(f"-> Erro ao consultar {acronym.upper()}: {e}")
                continue
        print("-> Processo não encontrado em nenhum tribunal.")
        return None
