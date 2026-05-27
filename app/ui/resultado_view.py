"""Componentes visuais para exibição dos resultados das consultas."""

import json
from typing import Any

import flet as ft

from app.services.cep_utils import CEP_CAMPOS_ENDERECO, extrair_dados_endereco
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


def extrair_dados_resultado(
    payload: dict[str, Any],
    *,
    tipo: str = "cpf",
) -> list[tuple[str, str]]:
    """Somente campos de dados (status/return/consumed vão na barra inferior)."""
    if payload.get("return") == "OK":
        dados = extrair_dados_endereco(payload) if tipo == "cep" else payload.get("result")
        if isinstance(dados, dict) and dados:
            itens: list[tuple[str, str]] = []
            if tipo == "cep":
                for chave in CEP_CAMPOS_ENDERECO:
                    if chave in dados and str(dados[chave]).strip() != "":
                        itens.append((ROTULOS_CEP[chave], str(dados[chave])))
            else:
                for chave, valor in dados.items():
                    rotulo = ROTULOS_CPF.get(chave, chave.replace("_", " ").title())
                    itens.append((rotulo, str(valor)))
            if itens:
                return itens

    return [("Detalhes", json.dumps(payload, ensure_ascii=False, indent=2))]


def criar_campo_resultado(page: ft.Page, label: str, valor: str) -> ft.Control:
    valor_str = valor if valor is not None else ""

    async def copiar(e: ft.ControlEvent) -> None:
        ok = await copiar_texto(e.page, valor_str)
        mostrar_feedback_copia(e.page, label, ok)

    return ft.Row(
        controls=[
            ft.TextField(
                label=label,
                value=valor_str,
                read_only=True,
                expand=True,
                multiline=len(valor_str) > 60,
                min_lines=1,
                max_lines=3 if len(valor_str) > 60 else 1,
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
    return [criar_campo_resultado(page, label, valor) for label, valor in itens]
