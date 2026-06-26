from unittest.mock import MagicMock

import pytest

from app.services.correios_service import CorreiosService


@pytest.fixture
def hub_mock():
    return MagicMock()


@pytest.fixture
def service(db, hub_mock):
    return CorreiosService(db, hub=hub_mock)


def test_calcular_frete_validacao_cep(service, hub_mock):
    resposta = service.calcular_frete(
        cep_origem="123",
        cep_destino="04785020",
        altura="10",
        largura="11",
        comprimento="17",
        peso="300",
        formato="1",
        tipo_servico="40010",
    )
    assert resposta["source"] == "validacao"
    assert resposta["data"]["return"] == "NOK"
    hub_mock.consultar_frete_correios.assert_not_called()


def test_calcular_frete_api(service, hub_mock, db):
    hub_mock.consultar_frete_correios.return_value = {
        "return": "OK",
        "status": "true",
        "message": "ok",
        "consumed": 1,
        "dados": {
            "servico": "SEDEX",
            "prazo_de_entrega": "1 dia(s)",
            "entrega_sabado": "Sim",
            "valor_total": "R$ 17,20",
        },
    }
    resposta = service.calcular_frete(
        cep_origem="30494310",
        cep_destino="04785020",
        altura="10",
        largura="11",
        comprimento="17",
        peso="300",
        formato="1",
        tipo_servico="40010",
    )
    assert resposta["source"] == "api"
    assert resposta["data"]["return"] == "OK"
    hub_mock.consultar_frete_correios.assert_called_once()

    segunda = service.calcular_frete(
        cep_origem="30494310",
        cep_destino="04785020",
        altura="10",
        largura="11",
        comprimento="17",
        peso="300",
        formato="1",
        tipo_servico="40010",
    )
    assert segunda["source"] == "local"
    assert hub_mock.consultar_frete_correios.call_count == 1


def test_rastrear_api(service, hub_mock):
    hub_mock.consultar_rastreio_correios.return_value = {
        "return": "OK",
        "status": "true",
        "message": "ok",
        "consumed": 1,
        "dados": [
            {
                "data": "25/02/2017 10:55",
                "local": "Sao Paulo/SP",
                "retorno": "Objeto postado",
            }
        ],
    }
    resposta = service.rastrear("AA123456789BR")
    assert resposta["source"] == "api"
    assert resposta["data"]["return"] == "OK"
    hub_mock.consultar_rastreio_correios.assert_called_once_with("AA123456789BR")


def test_rastrear_codigo_curto(service, hub_mock):
    resposta = service.rastrear("ABC")
    assert resposta["source"] == "validacao"
    hub_mock.consultar_rastreio_correios.assert_not_called()
