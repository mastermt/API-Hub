import asyncio
import sys

import flet as ft

from app.config import DB_PATH
from app.database.db import Database
from app.services.cep_service import CepService
from app.services.cnpj_service import CnpjService
from app.services.cpf_service import CpfService, formatar_data_nascimento
from app.ui.layout_helpers import (
    BarraStatus,
    criar_painel_duplo,
    linha_botoes_acao,
    mensagem_resultado_vazio,
)
from app.ui.resultado_view import montar_painel_resultado


def _configure_windows_event_loop() -> None:
    """Suprime ruído do Proactor no Windows quando o navegador fecha a conexão."""
    if sys.platform != "win32":
        return

    loop = asyncio.get_running_loop()
    default_handler = loop.get_exception_handler() or loop.default_exception_handler

    def _handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError):
            return
        message = context.get("message", "")
        if "_call_connection_lost" in message:
            return
        default_handler(context)

    loop.set_exception_handler(_handler)


def build_app(page: ft.Page) -> None:
    _configure_windows_event_loop()
    page.title = "API Consulta - Hub do Desenvolvedor"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 8
    page.spacing = 0

    db = Database(DB_PATH)
    service_cpf = CpfService(db)
    service_cnpj = CnpjService(db)
    service_cep = CepService(db)
    barra_status = BarraStatus()

    largura_campo = 280

    def limpar_resultado(coluna: ft.Column) -> None:
        coluna.controls = [mensagem_resultado_vazio()]

    campos_pesquisa: list[ft.TextField] = []

    async def focar_pesquisa(indice: int) -> None:
        if 0 <= indice < len(campos_pesquisa):
            campo = campos_pesquisa[indice]
            if not campo.disabled:
                await campo.focus()
        page.update()

    # --- Aba CPF ---
    cpf_field = ft.TextField(
        label="CPF",
        hint_text="Somente números (Enter para consultar)",
        width=largura_campo,
        max_length=14,
        dense=True,
    )
    data_field = ft.TextField(
        label="Data de nascimento",
        hint_text="DD/MM/AAAA ou 23091967 (Enter)",
        width=largura_campo,
        max_length=10,
        dense=True,
    )
    forcar_api_cpf = ft.Checkbox(
        label="Forçar API (ignorar cache)",
        value=False,
    )
    turbo_cpf = ft.Checkbox(label="Turbo (25 créditos)", value=False)
    resultado_cpf = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[mensagem_resultado_vazio()],
    )

    def exibir_cpf(payload: dict, source: str) -> None:
        resultado_cpf.controls = montar_painel_resultado(page, payload, tipo="cpf")
        barra_status.atualizar(payload, source)

    async def buscar_cpf(_: ft.ControlEvent) -> None:
        btn_cpf.disabled = True
        page.update()
        try:
            if data_field.value:
                fmt = formatar_data_nascimento(data_field.value)
                if fmt:
                    data_field.value = fmt
            resposta = await asyncio.to_thread(
                service_cpf.consultar,
                cpf_field.value or "",
                data_field.value,
                forcar_api=forcar_api_cpf.value,
                turbo=turbo_cpf.value,
            )
            exibir_cpf(resposta["data"], resposta["source"])
            barra_status.atualizar_totais(db.get_consumed_totals())
        finally:
            btn_cpf.disabled = False
            page.update()

    def limpar_cpf(_: ft.ControlEvent) -> None:
        cpf_field.value = ""
        data_field.value = ""
        forcar_api_cpf.value = False
        turbo_cpf.value = False
        limpar_resultado(resultado_cpf)
        barra_status.limpar()
        page.run_task(focar_pesquisa, 0)
        page.update()

    btn_cpf = ft.FilledButton("Consultar", icon=ft.Icons.SEARCH, on_click=buscar_cpf)
    btn_limpar_cpf = ft.OutlinedButton(
        "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar_cpf
    )
    cpf_field.on_submit = buscar_cpf
    data_field.on_submit = buscar_cpf

    painel_cpf = criar_painel_duplo(
        "Pesquisa",
        ft.Column(
            [
                cpf_field,
                data_field,
                forcar_api_cpf,
                turbo_cpf,
                linha_botoes_acao(btn_cpf, btn_limpar_cpf),
            ],
            spacing=8,
            tight=True,
        ),
        "Retorno",
        resultado_cpf,
    )
    campos_pesquisa.append(cpf_field)

    # --- Aba CNPJ ---
    cnpj_field = ft.TextField(
        label="CNPJ",
        hint_text="14 dígitos (Enter para consultar)",
        width=largura_campo,
        max_length=18,
        dense=True,
    )
    forcar_api_cnpj = ft.Checkbox(label="Forçar API (ignorar cache)", value=False)
    receita_direta_cnpj = ft.Checkbox(
        label="Receita direta (ignore_db, 2 créditos)",
        value=False,
    )
    ie_cnpj = ft.Dropdown(
        label="Inscrição Estadual (IE)",
        width=largura_campo,
        value="",
        options=[
            ft.DropdownOption(key="", text="Não consultar IE"),
            ft.DropdownOption(key="3", text="IE em cache (ie=3)"),
            ft.DropdownOption(key="1", text="IE online (ie=1, +2 créditos)"),
        ],
    )
    resultado_cnpj = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[mensagem_resultado_vazio()],
    )

    def exibir_cnpj(payload: dict, source: str) -> None:
        resultado_cnpj.controls = montar_painel_resultado(page, payload, tipo="cnpj")
        barra_status.atualizar(payload, source)

    async def buscar_cnpj(_: ft.ControlEvent) -> None:
        btn_cnpj.disabled = True
        page.update()
        try:
            ie_val = ie_cnpj.value or None
            if ie_val == "":
                ie_val = None
            resposta = await asyncio.to_thread(
                service_cnpj.consultar,
                cnpj_field.value or "",
                forcar_api=forcar_api_cnpj.value,
                receita_direta=receita_direta_cnpj.value,
                ie=ie_val,
            )
            exibir_cnpj(resposta["data"], resposta["source"])
            barra_status.atualizar_totais(db.get_consumed_totals())
        finally:
            btn_cnpj.disabled = False
            page.update()

    def limpar_cnpj(_: ft.ControlEvent) -> None:
        cnpj_field.value = ""
        forcar_api_cnpj.value = False
        receita_direta_cnpj.value = False
        ie_cnpj.value = ""
        limpar_resultado(resultado_cnpj)
        barra_status.limpar()
        page.run_task(focar_pesquisa, 1)
        page.update()

    btn_cnpj = ft.FilledButton("Consultar", icon=ft.Icons.SEARCH, on_click=buscar_cnpj)
    btn_limpar_cnpj = ft.OutlinedButton(
        "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar_cnpj
    )
    cnpj_field.on_submit = buscar_cnpj

    painel_cnpj = criar_painel_duplo(
        "Pesquisa",
        ft.Column(
            [
                cnpj_field,
                ft.Text(
                    "WSCNPJ1 — Receita Federal (timeout até 300s)",
                    size=11,
                    color=ft.Colors.GREY_700,
                ),
                forcar_api_cnpj,
                receita_direta_cnpj,
                ie_cnpj,
                linha_botoes_acao(btn_cnpj, btn_limpar_cnpj),
            ],
            spacing=8,
            tight=True,
        ),
        "Retorno",
        resultado_cnpj,
    )
    campos_pesquisa.append(cnpj_field)

    # --- Aba CEP ---
    cep_field = ft.TextField(
        label="CEP",
        hint_text="8 dígitos (Enter para consultar)",
        width=largura_campo,
        max_length=9,
        dense=True,
    )
    forcar_api_cep = ft.Checkbox(label="Forçar API (ignorar cache)", value=False)
    resultado_cep = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[mensagem_resultado_vazio()],
    )

    def exibir_cep(payload: dict, source: str) -> None:
        resultado_cep.controls = montar_painel_resultado(page, payload, tipo="cep")
        barra_status.atualizar(payload, source)

    async def buscar_cep(_: ft.ControlEvent) -> None:
        btn_cep.disabled = True
        page.update()
        try:
            resposta = await asyncio.to_thread(
                service_cep.consultar,
                cep_field.value or "",
                forcar_api=forcar_api_cep.value,
            )
            exibir_cep(resposta["data"], resposta["source"])
            barra_status.atualizar_totais(db.get_consumed_totals())
        finally:
            btn_cep.disabled = False
            page.update()

    def limpar_cep(_: ft.ControlEvent) -> None:
        cep_field.value = ""
        forcar_api_cep.value = False
        limpar_resultado(resultado_cep)
        barra_status.limpar()
        page.run_task(focar_pesquisa, 2)
        page.update()

    btn_cep = ft.FilledButton("Consultar", icon=ft.Icons.SEARCH, on_click=buscar_cep)
    btn_limpar_cep = ft.OutlinedButton(
        "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar_cep
    )
    cep_field.on_submit = buscar_cep

    painel_cep = criar_painel_duplo(
        "Pesquisa",
        ft.Column(
            [
                cep_field,
                ft.Text(
                    "WSCEP1J3 — busca nos Correios",
                    size=11,
                    color=ft.Colors.GREY_700,
                ),
                forcar_api_cep,
                linha_botoes_acao(btn_cep, btn_limpar_cep),
            ],
            spacing=8,
            tight=True,
        ),
        "Retorno",
        resultado_cep,
    )
    campos_pesquisa.append(cep_field)

    def painel_em_breve(nome: str, indice_aba: int) -> ft.Row:
        campo = ft.TextField(
            label=f"Consulta {nome}",
            hint_text="Em breve",
            width=largura_campo,
            disabled=True,
            dense=True,
        )
        resultado = ft.Column(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            controls=[mensagem_resultado_vazio()],
        )

        def limpar(_: ft.ControlEvent) -> None:
            campo.value = ""
            limpar_resultado(resultado)
            barra_status.limpar()
            page.run_task(focar_pesquisa, indice_aba)
            page.update()

        btn_limpar = ft.OutlinedButton(
            "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar
        )
        btn_consultar = ft.FilledButton(
            "Consultar",
            icon=ft.Icons.SEARCH,
            disabled=True,
        )

        campos_pesquisa.append(campo)

        return criar_painel_duplo(
            "Pesquisa",
            ft.Column(
                [
                    campo,
                    ft.Text("Serviço em desenvolvimento.", size=11, color=ft.Colors.GREY_700),
                    linha_botoes_acao(btn_consultar, btn_limpar),
                ],
                spacing=8,
                tight=True,
            ),
            "Retorno",
            resultado,
        )

    async def ao_mudar_aba(e: ft.ControlEvent) -> None:
        try:
            indice = int(e.data)
        except (TypeError, ValueError):
            indice = tabs.selected_index
        await focar_pesquisa(indice)

    tabs = ft.Tabs(
        length=5,
        expand=True,
        on_change=ao_mudar_aba,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="CPF", icon=ft.Icons.BADGE_OUTLINED),
                        ft.Tab(label="CNPJ", icon=ft.Icons.BUSINESS_OUTLINED),
                        ft.Tab(label="CEP", icon=ft.Icons.LOCATION_ON_OUTLINED),
                        ft.Tab(label="Correios", icon=ft.Icons.LOCAL_SHIPPING_OUTLINED),
                        ft.Tab(label="Outros", icon=ft.Icons.MORE_HORIZ),
                    ],
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        painel_cpf,
                        painel_cnpj,
                        painel_cep,
                        painel_em_breve("Correios", 3),
                        painel_em_breve("Outros", 4),
                    ],
                ),
            ],
        ),
    )

    barra_status.atualizar_totais(db.get_consumed_totals())

    page.add(
        ft.Column(
            [
                ft.Text(
                    "API Consulta — Hub do Desenvolvedor",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Paitom TIC - Pedro Tomaz Alves - 2026",
                    size=11,
                    color=ft.Colors.GREY_700,
                ),
                tabs,
                barra_status.control(),
            ],
            expand=True,
            spacing=6,
        )
    )

    page.run_task(focar_pesquisa, 0)
