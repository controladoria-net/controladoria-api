from datetime import datetime, timezone

from src.domain.entities.case import CNJNumber
from src.infra.external.gateway.datajud_gateway import DataJudGateway


def test_datajud_gateway_maps_formatted_case_number(monkeypatch):
    gateway = DataJudGateway()
    gateway.api_key = "dummy-key"
    gateway.base_url = "https://api.datajud.example"

    canonical_case_number = "0710802-55.2018.8.02.0001"
    payload = {
        "numeroProcesso": canonical_case_number,
        "tribunal": "TJAL",
        "classe": {"nome": "Classe Teste"},
        "orgaoJulgador": {"nome": "1ª Vara"},
        "dataAjuizamento": "2024-01-03T10:00:00Z",
        "grau": "2º Grau",
        "assuntos": [{"nome": "Assunto Teste"}],
        "movimentos": [
            {
                "dataHora": "2024-02-01T12:00:00Z",
                "nome": "Despacho",
                "complementosTabelados": [],
            }
        ],
    }

    def fake_post(url, headers, json, timeout):
        assert url == f"{gateway.base_url}/api_publica_tjal/_search"
        assert headers["Authorization"] == "ApiKey dummy-key"
        assert json == {"query": {"match": {"numeroProcesso": cnj.clean_number}}}
        assert timeout == 15

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"hits": {"hits": [{"_source": payload}]}}

        return FakeResponse()

    monkeypatch.setattr(
        "src.infra.external.gateway.datajud_gateway.requests.post", fake_post
    )

    cnj = CNJNumber.from_raw("07108025520188020001")

    legal_case = gateway.find_case_by_number(cnj, "tjal")

    assert legal_case is not None
    assert legal_case.case_number == canonical_case_number
    assert legal_case.latest_update == "Despacho"
    assert legal_case.movement_history is not None
    assert len(legal_case.movement_history) == 1
    first_movement = legal_case.movement_history[0]
    assert first_movement.description == "Despacho"
    assert first_movement.date == datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc)
