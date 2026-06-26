"""Testes de normalização CEP e serviço com cache."""

from unittest.mock import MagicMock

from app.services.cep_service import CepService, normalizar_cep
from app.services.cep_utils import normalizar_resposta_cep


def test_normalizar_cep_remove_formatacao():
    assert normalizar_cep("01310-100") == "01310100"


def test_normalizar_resposta_cep_sucesso_plano():
    raw = {
        "cep": "01310100",
        "logradouro": "Avenida Paulista",
        "bairro": "Bela Vista",
        "localidade": "São Paulo",
        "uf": "SP",
    }
    payload = normalizar_resposta_cep(raw)
    assert payload["return"] == "OK"
    assert payload["result"]["logradouro"] == "Avenida Paulista"


def test_cep_service_validacao():
    db = MagicMock()
    service = CepService(db, hub=MagicMock())
    resposta = service.consultar("123")
    assert resposta["source"] == "validacao"
    assert resposta["data"]["return"] == "NOK"


def test_cep_service_cache(db):
    hub = MagicMock()
    hub.consultar_cep.return_value = {
        "cep": "01310100",
        "logradouro": "Avenida Paulista",
        "localidade": "São Paulo",
        "uf": "SP",
    }
    service = CepService(db, hub=hub)

    primeira = service.consultar("01310-100")
    segunda = service.consultar("01310100")

    assert primeira["source"] == "api"
    assert segunda["source"] == "local"
    hub.consultar_cep.assert_called_once()
