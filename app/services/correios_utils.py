"""Constantes e normalização dos webservices Correios (WSFRETEJ / WSRASTREIOJ)."""

from __future__ import annotations

import json
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


def extrair_mensagem_hub(raw: dict[str, Any]) -> str:
    """Extrai mensagem legível do envelope do Hub (string, dict ou vazio)."""
    msg = raw.get("message")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()
    if isinstance(msg, dict) and msg:
        for chave in ("texto", "descricao", "mensagem", "erro"):
            valor = msg.get(chave)
            if valor:
                return str(valor).strip()
        return json.dumps(msg, ensure_ascii=False)
    if isinstance(msg, list) and msg:
        return "; ".join(str(item) for item in msg if item)

    for chave in ("mensagem", "descricao", "erro_msg"):
        valor = raw.get(chave)
        if valor:
            return str(valor).strip()
    return ""


def _tem_dados_validos(raw: dict[str, Any]) -> bool:
    dados = raw.get("dados")
    if isinstance(dados, list) and dados:
        return True
    if isinstance(dados, dict) and dados:
        return True
    result = raw.get("result")
    if isinstance(result, list) and result:
        return True
    if isinstance(result, dict) and result:
        return True
    return False


def _status_falha(raw: dict[str, Any]) -> bool:
    erro = raw.get("erro")
    if erro in ("sim", "yes", "1", 1, True):
        return True
    if raw.get("return") == "NOK":
        return True
    status = raw.get("status")
    if status is False:
        return True
    if isinstance(status, str) and status.lower() in ("false", "0", "nao", "não", "nok"):
        return True
    if isinstance(status, int) and status == 0:
        return True
    return False


def _status_ok(raw: dict[str, Any]) -> bool:
    if _status_falha(raw):
        return False
    if raw.get("return") == "OK":
        return True
    if _tem_dados_validos(raw):
        return True

    status = raw.get("status")
    if isinstance(status, bool):
        return status
    if isinstance(status, str):
        return status.lower() in ("true", "1", "sim")
    if isinstance(status, int):
        return status != 0

    erro = raw.get("erro")
    if erro in ("nao", "não", "no", "0"):
        return True
    return False


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
    if isinstance(dados, dict):
        for chave in ("eventos", "lista", "historico"):
            eventos = dados.get(chave)
            if isinstance(eventos, list):
                return [item for item in eventos if isinstance(item, dict)]
    result = payload.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    return []


def _mensagem_erro_padrao(raw: dict[str, Any]) -> str:
    servico = str(raw.get("servico") or "").lower()
    if servico == "rastreamento" or "rastre" in servico:
        return (
            "WSRASTREIOJ (JSON): o Hub respondeu NOK sem detalhes. "
            "A URL e os parâmetros estão corretos (servico=rastreamento, codigo_rastreamento). "
            "Verifique no painel do Hub se o plano inclui rastreio e teste o mesmo código no site deles."
        )
    return "Consulta não retornou."


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
    message = extrair_mensagem_hub(raw)
    return_code = raw.get("return", "")

    if return_code == "NOK" or not _status_ok(raw):
        return {
            "status": False,
            "return": "NOK",
            "message": message or _mensagem_erro_padrao(raw),
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
