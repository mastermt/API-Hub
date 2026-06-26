"""Testes de formatação e validação de CPF."""

import pytest

from app.services.cpf_service import (
    formatar_data_nascimento,
    normalizar_cpf,
    validar_data_nascimento,
)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("123.456.789-01", "12345678901"),
        ("12345678901", "12345678901"),
    ],
)
def test_normalizar_cpf(entrada, esperado):
    assert normalizar_cpf(entrada) == esperado


def test_validar_data_nascimento_valida():
    assert validar_data_nascimento("23/09/1967") is True


def test_validar_data_nascimento_invalida():
    assert validar_data_nascimento("31/02/2020") is False
    assert validar_data_nascimento("abc") is False


def test_formatar_data_nascimento_digitos():
    assert formatar_data_nascimento("23091967") == "23/09/1967"


def test_formatar_data_nascimento_ja_formatada():
    assert formatar_data_nascimento("23/09/1967") == "23/09/1967"


def test_formatar_data_nascimento_invalida():
    assert formatar_data_nascimento("99999999") is None
