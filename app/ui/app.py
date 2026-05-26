import json

import flet as ft

from app.config import DB_PATH
from app.database.db import Database
from app.services.cpf_service import CpfService, formatar_data_nascimento
from app.services.cep_service import CepService
from app.services.cep_utils import CEP_CAMPOS_ENDERECO, extrair_dados_endereco


def build_app(page: ft.Page) -> None:
    page.title = "API Consulta - Hub do Desenvolvedor"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO

    db = Database(DB_PATH)
    service_cpf = CpfService(db)
    service_cep = CepService(db)

    cpf_field = ft.TextField(
        label="CPF",
        hint_text="Somente números",
        width=320,
        max_length=14,
    )
    cep_field = ft.TextField(
        label="CEP",
        hint_text="Somente números (8 dígitos)",
        width=320,
        max_length=9,
    )
    data_field = ft.TextField(
        label="Data de nascimento",
        hint_text="DD/MM/AAAA ou 8 dígitos (ex.: 23091967)",
        width=320,
        max_length=10,
    )
    forcar_api = ft.Checkbox(label="Forçar consulta na API (ignore cache local)")
    turbo = ft.Checkbox(label="Modo Turbo (25 créditos, timeout 30s)")

    origem_text = ft.Text("", size=13, color=ft.Colors.BLUE_GREY_700)
    consumo_text = ft.Text("", size=13)
    resultado = ft.Text("", selectable=True, size=14)

    def atualizar_consumo() -> None:
        totais = db.get_consumed_totals()
        consumo_text.value = (
            f"Créditos consumidos (local): CPF {totais['cpf']} | "
            f"CNPJ {totais['cnpj']} | CEP {totais['cep']} | "
            f"Correios {totais['correios']} | Outros {totais['outros']}"
        )

    def formatar_resultado(payload: dict, source: str, *, tipo: str = "cpf") -> str:
        linhas = [
            f"Origem: {source}",
            f"Retorno: {payload.get('return', '-')}",
            f"Mensagem: {payload.get('message') or '-'}",
            f"Créditos desta consulta: {payload.get('consumed', 0)}",
            "",
        ]

        if payload.get("return") == "OK":
            dados = extrair_dados_endereco(payload) if tipo == "cep" else payload.get("result")
            if isinstance(dados, dict) and dados:
                rotulos = {
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
                chaves = CEP_CAMPOS_ENDERECO if tipo == "cep" else dados.keys()
                for chave in chaves:
                    if chave in dados:
                        rotulo = rotulos.get(chave, chave) if tipo == "cep" else chave
                        linhas.append(f"{rotulo}: {dados[chave]}")
                return "\n".join(linhas)

            result = payload.get("result")
            if isinstance(result, dict):
                for chave, valor in result.items():
                    linhas.append(f"{chave}: {valor}")
                return "\n".join(linhas)

        linhas.append(json.dumps(payload, ensure_ascii=False, indent=2))
        return "\n".join(linhas)

    async def buscar_cpf(_: ft.ControlEvent) -> None:
        btn_buscar_cpf.disabled = True
        page.update()

        try:
            if data_field.value:
                data_formatada = formatar_data_nascimento(data_field.value)
                if data_formatada:
                    data_field.value = data_formatada

            resposta = service_cpf.consultar(
                cpf_field.value or "",
                data_field.value,
                forcar_api=forcar_api.value,
                turbo=turbo.value,
            )
            payload = resposta["data"]
            source = resposta["source"]
            origem_map = {
                "local": "Cache local (banco de dados)",
                "api": "API Hub do Desenvolvedor",
                "validacao": "Validação local",
                "erro": "Erro",
            }
            origem_text.value = origem_map.get(source, source)
            resultado.value = formatar_resultado(payload, source)
            atualizar_consumo()
        finally:
            btn_buscar_cpf.disabled = False
            page.update()

    async def buscar_cep(_: ft.ControlEvent) -> None:
        btn_buscar_cep.disabled = True
        page.update()

        try:
            resposta = service_cep.consultar(
                cep_field.value or "",
                forcar_api=forcar_api.value,
            )
            payload = resposta["data"]
            source = resposta["source"]
            origem_map = {
                "local": "Cache local (banco de dados)",
                "api": "API Hub do Desenvolvedor",
                "validacao": "Validação local",
                "erro": "Erro",
            }
            origem_text.value = origem_map.get(source, source)
            resultado.value = formatar_resultado(payload, source, tipo="cep")
            atualizar_consumo()
        finally:
            btn_buscar_cep.disabled = False
            page.update()

    btn_buscar_cpf = ft.ElevatedButton(
        "Consultar CPF", icon=ft.Icons.SEARCH, on_click=buscar_cpf
    )
    btn_buscar_cep = ft.ElevatedButton(
        "Consultar CEP", icon=ft.Icons.SEARCH, on_click=buscar_cep
    )
    atualizar_consumo()

    page.add(
        ft.Text("Consulta CPF e CEP", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("Hub do Desenvolvedor — cache local antes da API", size=14, color=ft.Colors.GREY_700),
        ft.Divider(),
        ft.Text("Consulta CPF", size=18, weight=ft.FontWeight.W_600),
        ft.Row([cpf_field, data_field], wrap=True, spacing=16),
        ft.Row([forcar_api, turbo], wrap=True),
        btn_buscar_cpf,
        ft.Divider(),
        ft.Text("Consulta CEP (WSCEP1J3 — Correios)", size=18, weight=ft.FontWeight.W_600),
        ft.Text(
            "Busca direto nos Correios. Informe somente números no CEP.",
            size=12,
            color=ft.Colors.GREY_700,
        ),
        ft.Row([cep_field], wrap=True, spacing=16),
        btn_buscar_cep,
        origem_text,
        consumo_text,
        ft.Divider(),
        ft.Text("Resultado", size=18, weight=ft.FontWeight.W_600),
        resultado,
        ft.Container(height=16),
        ft.Text("CNPJ, Correios e Outros: em breve", size=12, italic=True, color=ft.Colors.GREY_600),
    )
