from unittest.mock import MagicMock, patch

from app.api.hub_client import HubClient


@patch("app.api.hub_client.httpx.Client")
def test_consultar_frete_correios_parametros(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = {"return": "OK"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    client = HubClient(token="token-teste")
    client.consultar_frete_correios(
        cep_origem="30494310",
        cep_destino="04785020",
        altura="10",
        largura="11",
        comprimento="17",
        peso="300",
        formato="1",
        tipo_servico="40010",
        aviso_recebimento=True,
        mao_propria=True,
    )

    mock_client.get.assert_called_once()
    _, kwargs = mock_client.get.call_args
    params = kwargs["params"]
    assert params["servico"] == "calculoFrete"
    assert params["cepOrigem"] == "30494310"
    assert params["tipoServico"] == "40010"
    assert params["avisoRecebimento"] == "S"
    assert params["maoPropria"] == "S"
    assert params["token"] == "token-teste"


@patch("app.api.hub_client.httpx.Client")
def test_consultar_rastreio_correios_parametros(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = {"return": "OK"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    client = HubClient(token="token-teste")
    client.consultar_rastreio_correios("AA123456789BR")

    _, kwargs = mock_client.get.call_args
    params = kwargs["params"]
    assert params["servico"] == "rastreamento"
    assert params["codigo_rastreamento"] == "AA123456789BR"
