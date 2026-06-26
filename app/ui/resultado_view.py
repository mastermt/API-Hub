"""Componentes visuais para exibição dos resultados das consultas."""

import json
import re
import unicodedata
from typing import Any

import flet as ft

from app.services.cep_utils import CEP_CAMPOS_ENDERECO, extrair_dados_endereco
from app.services.cnpj_utils import extrair_campos_cnpj
from app.services.correios_utils import CAMPOS_FRETE, extrair_dados_frete, extrair_eventos_rastreio
from app.ui.clipboard_util import copiar_texto, mostrar_feedback_copia

ROTULOS_CEP = {
    "cep": "CEP",
    "logradouro": "Logradouro",
    "complemento": "Complemento",
    "bairro": "Bairro",
    "localidade": "Cidade",
    "uf": "UF",
    "unidade": "Unidade",
    "ibge": "IBGE",
    "gia": "GIA",
}

ROTULOS_CPF = {
    "numero_de_cpf": "CPF",
    "nome_da_pf": "Nome",
    "data_nascimento": "Data de nascimento",
    "situacao_cadastral": "Situação cadastral",
    "data_inscricao": "Data de inscrição",
    "digito_verificador": "Dígito verificador",
    "comprovante_emitido": "Comprovante emitido",
    "comprovante_emitido_data": "Comprovante emitido em",
}

ROTULOS_FRETE = {
    "servico": "Serviço",
    "prazo_de_entrega": "Prazo de entrega",
    "entrega_sabado": "Entrega sábado",
    "valor_total": "Valor total",
}


def formatar_eventos_rastreio(eventos: list[dict[str, Any]]) -> str:
    linhas: list[str] = []
    for evento in eventos:
        data = str(evento.get("data") or "").strip()
        local = str(evento.get("local") or "").strip()
        retorno = str(evento.get("retorno") or "").strip()
        partes = [p for p in (data, local, retorno) if p]
        if partes:
            linhas.append(" — ".join(partes))
    return "\n".join(linhas)


def _somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _nome_para_ascii_maiusculo(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFKD", texto)
    ascii_txt = sem_acentos.encode("ascii", "ignore").decode("ascii")
    return ascii_txt.upper()


def valor_para_copia(valor: str, campo: str | None, *, tipo: str = "cpf") -> str:
    """Formata o valor conforme o campo antes de copiar."""
    if not campo:
        return valor

    if tipo == "cpf":
        if campo == "numero_de_cpf":
            return _somente_digitos(valor)
        if campo == "nome_da_pf":
            return _nome_para_ascii_maiusculo(valor)

    if tipo == "cep" and campo == "cep":
        return _somente_digitos(valor)

    if tipo == "cnpj":
        if campo == "numero_de_inscricao":
            return _somente_digitos(valor)
        if campo in ("nome", "fantasia"):
            return _nome_para_ascii_maiusculo(valor)
        if campo == "cep":
            return _somente_digitos(valor)

    return valor


def extrair_dados_resultado(
    payload: dict[str, Any],
    *,
    tipo: str = "cpf",
) -> list[tuple[str, str, str | None]]:
    """Retorna (rótulo, valor exibido, chave do campo)."""
    if payload.get("return") == "OK":
        if tipo == "cep":
            dados = extrair_dados_endereco(payload)
            if isinstance(dados, dict) and dados:
                itens: list[tuple[str, str, str | None]] = []
                for chave in CEP_CAMPOS_ENDERECO:
                    if chave in dados and str(dados[chave]).strip() != "":
                        itens.append((ROTULOS_CEP[chave], str(dados[chave]), chave))
                if itens:
                    return itens
        elif tipo == "cnpj":
            result = payload.get("result")
            if isinstance(result, dict):
                itens_cnpj = extrair_campos_cnpj(result)
                if itens_cnpj:
                    return itens_cnpj
        elif tipo == "correios_frete":
            dados = extrair_dados_frete(payload)
            if dados:
                itens_frete: list[tuple[str, str, str | None]] = []
                for chave in CAMPOS_FRETE:
                    if chave in dados and str(dados[chave]).strip() != "":
                        itens_frete.append(
                            (ROTULOS_FRETE[chave], str(dados[chave]), chave)
                        )
                if itens_frete:
                    return itens_frete
        elif tipo == "correios_rastreio":
            eventos = extrair_eventos_rastreio(payload)
            itens_rastreio: list[tuple[str, str, str | None]] = []
            imagem = payload.get("imagem_status")
            if imagem:
                itens_rastreio.append(("Imagem status", str(imagem), "imagem_status"))
            if eventos:
                itens_rastreio.append(
                    ("Histórico", formatar_eventos_rastreio(eventos), "historico")
                )
            if itens_rastreio:
                return itens_rastreio
        else:
            dados = payload.get("result")
            if isinstance(dados, dict) and dados:
                itens = []
                for chave, valor in dados.items():
                    rotulo = ROTULOS_CPF.get(chave, chave.replace("_", " ").title())
                    itens.append((rotulo, str(valor), chave))
                if itens:
                    return itens

    return [("Detalhes", json.dumps(payload, ensure_ascii=False, indent=2), None)]


def criar_campo_resultado(
    page: ft.Page,
    label: str,
    valor: str,
    *,
    campo: str | None = None,
    tipo: str = "cpf",
) -> ft.Control:
    valor_str = valor if valor is not None else ""

    async def copiar(e: ft.ControlEvent) -> None:
        texto_copia = valor_para_copia(valor_str, campo, tipo=tipo)
        ok = await copiar_texto(e.page, texto_copia)
        mostrar_feedback_copia(e.page, label, ok)

    return ft.Row(
        controls=[
            ft.TextField(
                label=label,
                value=valor_str,
                read_only=True,
                expand=True,
                multiline=len(valor_str) > 60 or "\n" in valor_str,
                min_lines=1,
                max_lines=6 if len(valor_str) > 60 or "\n" in valor_str else 1,
                dense=True,
            ),
            ft.IconButton(
                icon=ft.Icons.CONTENT_COPY_OUTLINED,
                tooltip=f"Copiar {label}",
                on_click=copiar,
            ),
        ],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )


def montar_painel_resultado(
    page: ft.Page,
    payload: dict[str, Any],
    *,
    tipo: str = "cpf",
) -> list[ft.Control]:
    itens = extrair_dados_resultado(payload, tipo=tipo)
    if not itens:
        return [ft.Text("Nenhum dado retornado.", size=13, color=ft.Colors.GREY_700)]
    return [
        criar_campo_resultado(page, label, valor, campo=campo, tipo=tipo)
        for label, valor, campo in itens
    ]
