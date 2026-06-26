from app.services.correios_utils import (
    chave_cache_frete,
    extrair_dados_frete,
    extrair_eventos_rastreio,
    normalizar_codigo_rastreio,
    normalizar_resposta_correios,
)


def test_normalizar_codigo_rastreio():
    assert normalizar_codigo_rastreio(" aa 123456789 br ") == "AA123456789BR"


def test_chave_cache_frete_inclui_parametros():
    chave = chave_cache_frete(
        cep_origem="30494310",
        cep_destino="04785020",
        altura="10",
        largura="11",
        comprimento="17",
        peso="300",
        formato="1",
        tipo_servico="40010",
        aviso_recebimento=True,
        mao_propria=False,
    )
    assert "frete|30494310|04785020" in chave
    assert "ar=S" in chave


def test_normalizar_resposta_frete_sucesso():
    raw = {
        "erro": "nao",
        "status": "true",
        "return": "OK",
        "message": "Imprimindo resultado.",
        "consumed": 2,
        "dados": {
            "servico": "SEDEX",
            "prazo_de_entrega": "1 dia(s)",
            "entrega_sabado": "Sim",
            "valor_total": "R$ 17,20",
        },
    }
    payload = normalizar_resposta_correios(raw)
    assert payload["return"] == "OK"
    assert payload["status"] is True
    assert payload["consumed"] == 2
    assert extrair_dados_frete(payload)["servico"] == "SEDEX"


def test_normalizar_resposta_rastreio_sucesso():
    raw = {
        "erro": "nao",
        "status": "true",
        "return": "OK",
        "message": "Dados de rastreio encontrados.",
        "imagem_status": "http://example.com/entrega.gif",
        "dados": [
            {
                "data": "02/03/2017 15:29",
                "local": "Brasilia/DF",
                "retorno": "Objeto entregue ao destinatário",
            }
        ],
    }
    payload = normalizar_resposta_correios(raw)
    eventos = extrair_eventos_rastreio(payload)
    assert len(eventos) == 1
    assert eventos[0]["local"] == "Brasilia/DF"
    assert payload["imagem_status"] == "http://example.com/entrega.gif"


def test_normalizar_resposta_erro():
    raw = {"return": "NOK", "message": "Token inválido", "consumed": 0}
    payload = normalizar_resposta_correios(raw)
    assert payload["return"] == "NOK"
    assert payload["status"] is False
