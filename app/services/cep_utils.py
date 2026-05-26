"""Normalização do retorno WSCEP1J3 (Hub do Desenvolvedor)."""

from typing import Any

# Campos do endereço no retorno plano de sucesso (exemplo oficial).
CEP_CAMPOS_ENDERECO = (
    "cep",
    "logradouro",
    "complemento",
    "bairro",
    "localidade",
    "uf",
    "unidade",
    "ibge",
    "gia",
)


def extrair_dados_endereco(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("result")
    if isinstance(result, dict):
        return result
    return {k: payload[k] for k in CEP_CAMPOS_ENDERECO if k in payload}


def eh_resposta_sucesso_plana(payload: dict[str, Any]) -> bool:
    """Sucesso sem envelope: JSON plano com dados de endereço."""
    if payload.get("return") == "NOK":
        return False
    dados = extrair_dados_endereco(payload)
    return bool(dados.get("logradouro") or dados.get("localidade"))


def normalizar_resposta_cep(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Unifica retornos do WSCEP1J3:
    - Sucesso: JSON plano (cep, logradouro, bairro, ...)
    - Erro: return=NOK + message (e opcionalmente consumed)
    - Envelope: return=OK + result (quando existir)
    """
    if not raw:
        return {
            "status": False,
            "return": "NOK",
            "message": "Resposta vazia da API.",
            "consumed": 0,
        }

    return_code = raw.get("return")
    consumed = int(raw.get("consumed") or 0)
    message = raw.get("message", "")

    if return_code == "NOK":
        return {
            "status": False,
            "return": "NOK",
            "message": message or "Consulta não retornou.",
            "consumed": consumed,
        }

    if return_code == "OK":
        return {
            "status": True,
            "return": "OK",
            "message": message,
            "consumed": consumed,
            "result": extrair_dados_endereco(raw),
        }

    if eh_resposta_sucesso_plana(raw):
        return {
            "status": True,
            "return": "OK",
            "message": message,
            "consumed": consumed,
            "result": extrair_dados_endereco(raw),
        }

    if message:
        return {
            "status": False,
            "return": "NOK",
            "message": message,
            "consumed": consumed,
        }

    return {
        "status": False,
        "return": "NOK",
        "message": "Formato de resposta não reconhecido.",
        "consumed": consumed,
    }
