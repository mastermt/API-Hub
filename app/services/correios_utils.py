"""Constantes e normalização dos webservices Correios (WSFRETEJ / WSRASTREIOJ)."""

from __future__ import annotations

from typing import Any

TIPOS_SERVICO_FRETE: dict[str, str] = {
    "40010": "SEDEX",
    "40215": "SEDEX 10",
    "40045": "SEDEX a Cobrar",
    "40290": "SEDEX HOJE",
    "41106": "PAC",
}

FORMATOS_EMBALAGEM: dict[str, str] = {
    "1": "Caixa/pacote",
    "2": "Rolo/Prisma",
    "3": "Envelope",
}

CAMPOS_FRETE = (
    "servico",
    "prazo_de_entrega",
    "entrega_sabado",
    "valor_total",
)


def normalizar_cep(cep: str) -> str:
    import re

    return re.sub(r"\D", "", cep)


def normalizar_codigo_rastreio(codigo: str) -> str:
    return "".join(codigo.split()).upper()


def _status_ok(raw: dict[str, Any]) -> bool:
    if raw.get("erro") == "sim":
        return False
    if raw.get("return") == "NOK":
        return False
    status = raw.get("status")
    if isinstance(status, bool):
        return status
    if isinstance(status, str):
        return status.lower() in ("true", "1", "sim")
    return raw.get("return") == "OK"


def extrair_dados_frete(payload: dict[str, Any]) -> dict[str, Any]:
    dados = payload.get("dados")
    if isinstance(dados, dict):
        return dados
    result = payload.get("result")
    if isinstance(result, dict):
        return result
    return {}


def extrair_eventos_rastreio(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dados = payload.get("dados")
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    result = payload.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    return []


def chave_cache_frete(
    *,
    cep_origem: str,
    cep_destino: str,
    altura: str,
    largura: str,
    comprimento: str,
    peso: str,
    formato: str,
    tipo_servico: str,
    aviso_recebimento: bool,
    mao_propria: bool,
) -> str:
    flags = []
    if aviso_recebimento:
        flags.append("ar=S")
    if mao_propria:
        flags.append("mp=S")
    flag_txt = ",".join(flags)
    return (
        f"frete|{cep_origem}|{cep_destino}|{altura}|{largura}|{comprimento}|"
        f"{peso}|{formato}|{tipo_servico}|{flag_txt}"
    )


def normalizar_resposta_correios(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw:
        return {
            "status": False,
            "return": "NOK",
            "message": "Resposta vazia da API.",
            "consumed": 0,
        }

    consumed = int(raw.get("consumed") or 0)
    message = str(raw.get("message") or "")
    return_code = raw.get("return", "")

    if return_code == "NOK" or not _status_ok(raw):
        return {
            "status": False,
            "return": "NOK",
            "message": message or "Consulta não retornou.",
            "consumed": consumed,
        }

    payload: dict[str, Any] = {
        "status": True,
        "return": "OK",
        "message": message,
        "consumed": consumed,
    }

    dados = raw.get("dados")
    if dados is not None:
        payload["dados"] = dados
    if raw.get("imagem_status"):
        payload["imagem_status"] = raw["imagem_status"]

    frete = extrair_dados_frete(payload)
    if frete:
        payload["result"] = frete

    eventos = extrair_eventos_rastreio(payload)
    if eventos:
        payload["result"] = eventos

    return payload
