import os
from typing import Dict, Optional
from dotenv import load_dotenv
import requests

from src.domain.entities.case import CNJNumber, LegalCase
from src.domain.gateway.legal_case_gateway import LegalCaseGateway
from src.infra.external.dto.legal_case_dto import LegalCaseRawDTO
from src.infra.external.mapper.legal_case_mapper import LegalCaseMapper

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

    def _get_headers(self) -> Dict[str, str]:
        """Cria o cabeçalho padrão para as requisições."""
        return {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

    def find_case_by_number(
        self, case_number: CNJNumber, court_acronym: str
    ) -> Optional[LegalCase]:
        payload = {"query": {"match": {"numeroProcesso": case_number.clean_number}}}
        headers = self._get_headers()

        url = f"{self.base_url}/api_publica_{court_acronym}/_search"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            if hits := data.get("hits", {}).get("hits", []):
                print(
                    f"-> Processo encontrado em {court_acronym.upper()}! Mapeando dados..."
                )
                dto = LegalCaseRawDTO.from_dict(hits[0]["_source"])
                return LegalCaseMapper.from_dto_to_domain(dto)
        except requests.exceptions.RequestException as e:
            print(f"-> Erro ao consultar {court_acronym.upper()}: {e}")

        print("-> Processo não encontrado em nenhum tribunal.")
        return None
