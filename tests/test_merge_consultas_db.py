"""Testes da mesclagem de consultas.db."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from merge_consultas_db import mesclar_por_chave, payload_sucesso


def test_payload_sucesso_cpf_ok():
    payload = {
        "status": True,
        "return": "OK",
        "result": {"numero_de_cpf": "12345678901", "nome_da_pf": "TESTE"},
        "consumed": 1,
    }
    assert payload_sucesso(json.dumps(payload), return_code="OK", status=1)


def test_payload_sucesso_cpf_falha():
    payload = {
        "status": False,
        "return": "NOK",
        "message": "CPF inválido",
        "consumed": 0,
    }
    assert not payload_sucesso(json.dumps(payload), return_code="NOK", status=0)


def test_mesclar_por_chave_sem_duplicar_cpf():
    registros = [
        {
            "cpf": "12345678901",
            "response_json": json.dumps({"return": "OK", "status": True, "result": {}}),
            "return_code": "OK",
            "status": 1,
            "updated_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "cpf": "12345678901",
            "response_json": json.dumps(
                {"return": "OK", "status": True, "result": {"nome_da_pf": "NOVO"}}
            ),
            "return_code": "OK",
            "status": 1,
            "updated_at": "2026-06-01T00:00:00+00:00",
        },
        {
            "cpf": "12345678901",
            "response_json": json.dumps({"return": "NOK", "status": False}),
            "return_code": "NOK",
            "status": 0,
            "updated_at": "2026-12-01T00:00:00+00:00",
        },
    ]

    mesclados = mesclar_por_chave(registros, lambda r: (r["cpf"],), filtrar_sucesso=True)

    assert len(mesclados) == 1
    assert "NOVO" in mesclados[0]["response_json"]


def test_mesclar_ignora_cpf_com_falha():
    registros = [
        {
            "cpf": "99999999999",
            "response_json": json.dumps({"return": "NOK", "status": False}),
            "return_code": "NOK",
            "status": 0,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    ]

    mesclados = mesclar_por_chave(registros, lambda r: (r["cpf"],), filtrar_sucesso=True)
    assert mesclados == []
