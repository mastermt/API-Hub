"""Testes do banco SQLite e cache local."""

from app.database.db import Database


def test_save_e_get_cep(db):
    payload = {
        "status": True,
        "return": "OK",
        "message": "ok",
        "consumed": 1,
        "result": {"cep": "01310100", "logradouro": "Rua Teste"},
    }
    db.save_cep("01310100", payload)
    cached = db.get_cep("01310100")

    assert cached is not None
    assert cached["source"] == "local"
    assert cached["data"]["consumed"] == 0
    assert cached["data"]["result"]["logradouro"] == "Rua Teste"


def test_register_consumption_atualiza_totais(db):
    db.register_consumption("cep", "01310100", 2, origem="api")
    totais = db.get_consumed_totals()
    assert totais["cep"] == 2


def test_save_correios_cache(db):
    payload = {
        "status": True,
        "return": "OK",
        "message": "ok",
        "consumed": 1,
        "dados": [{"retorno": "Objeto postado"}],
    }
    db.save_correios("AA123456789BR", "rastreio", payload)
    cached = db.get_correios("AA123456789BR", "rastreio")

    assert cached is not None
    assert cached["source"] == "local"
    assert cached["data"]["consumed"] == 0
