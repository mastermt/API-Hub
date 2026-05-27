import flet as ft

from app.config import DB_PATH
from app.database.db import Database
from app.services.cep_service import CepService
from app.services.cpf_service import CpfService, formatar_data_nascimento
from app.ui.layout_helpers import (
    BarraStatus,
    criar_painel_duplo,
    linha_botoes_acao,
    mensagem_resultado_vazio,
)
from app.ui.resultado_view import montar_painel_resultado


def build_app(page: ft.Page) -> None:
    page.title = "API Consulta - Hub do Desenvolvedor"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 8
    page.spacing = 0

    db = Database(DB_PATH)
    service_cpf = CpfService(db)
    service_cep = CepService(db)
    barra_status = BarraStatus()

    largura_campo = 280

    def limpar_resultado(coluna: ft.Column) -> None:
        coluna.controls = [mensagem_resultado_vazio()]

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
            resposta = service_cpf.consultar(
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
            resposta = service_cep.consultar(
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

    def painel_em_breve(nome: str) -> ft.Row:
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
            page.update()

        btn_limpar = ft.OutlinedButton(
            "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar
        )
        btn_consultar = ft.FilledButton(
            "Consultar",
            icon=ft.Icons.SEARCH,
            disabled=True,
        )

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

    tabs = ft.Tabs(
        length=5,
        expand=True,
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
                        painel_em_breve("CNPJ"),
                        painel_cep,
                        painel_em_breve("Correios"),
                        painel_em_breve("Outros"),
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
                    "Cache local antes da API",
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
