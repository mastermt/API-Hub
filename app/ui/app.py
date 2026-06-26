import asyncio
import sys

import flet as ft

from app.config import DB_PATH
from app.database.db import Database
from app.services.cep_service import CepService
from app.services.cnpj_service import CnpjService
from app.services.correios_service import CorreiosService
from app.services.correios_utils import FORMATOS_EMBALAGEM, TIPOS_SERVICO_FRETE
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
    service_correios = CorreiosService(db)
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

    # --- Aba Correios (Frete + Rastreio) ---
    campo_largura_pequeno = 120

    frete_cep_origem = ft.TextField(
        label="CEP origem",
        hint_text="8 dígitos",
        width=campo_largura_pequeno,
        max_length=9,
        dense=True,
    )
    frete_cep_destino = ft.TextField(
        label="CEP destino",
        hint_text="8 dígitos",
        width=campo_largura_pequeno,
        max_length=9,
        dense=True,
    )
    frete_altura = ft.TextField(label="Altura (cm)", width=90, dense=True, value="10")
    frete_largura = ft.TextField(label="Largura (cm)", width=90, dense=True, value="11")
    frete_comprimento = ft.TextField(
        label="Comprimento (cm)", width=110, dense=True, value="17"
    )
    frete_peso = ft.TextField(label="Peso (g)", width=90, dense=True, value="300")
    frete_formato = ft.Dropdown(
        label="Formato",
        width=180,
        value="1",
        options=[
            ft.DropdownOption(key=k, text=v) for k, v in FORMATOS_EMBALAGEM.items()
        ],
    )
    frete_tipo_servico = ft.Dropdown(
        label="Serviço",
        width=200,
        value="40010",
        options=[
            ft.DropdownOption(key=k, text=f"{v} ({k})")
            for k, v in TIPOS_SERVICO_FRETE.items()
        ],
    )
    frete_aviso_recebimento = ft.Checkbox(label="Aviso de recebimento", value=False)
    frete_mao_propria = ft.Checkbox(label="Mãos próprias", value=False)
    forcar_api_frete = ft.Checkbox(label="Forçar API (ignorar cache)", value=False)
    resultado_frete = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[mensagem_resultado_vazio()],
    )

    def exibir_frete(payload: dict, source: str) -> None:
        resultado_frete.controls = montar_painel_resultado(
            page, payload, tipo="correios_frete"
        )
        barra_status.atualizar(payload, source)

    async def buscar_frete(_: ft.ControlEvent) -> None:
        btn_frete.disabled = True
        page.update()
        try:
            resposta = await asyncio.to_thread(
                service_correios.calcular_frete,
                cep_origem=frete_cep_origem.value or "",
                cep_destino=frete_cep_destino.value or "",
                altura=frete_altura.value or "",
                largura=frete_largura.value or "",
                comprimento=frete_comprimento.value or "",
                peso=frete_peso.value or "",
                formato=frete_formato.value or "1",
                tipo_servico=frete_tipo_servico.value or "40010",
                aviso_recebimento=frete_aviso_recebimento.value,
                mao_propria=frete_mao_propria.value,
                forcar_api=forcar_api_frete.value,
            )
            exibir_frete(resposta["data"], resposta["source"])
            barra_status.atualizar_totais(db.get_consumed_totals())
        finally:
            btn_frete.disabled = False
            page.update()

    def limpar_frete(_: ft.ControlEvent) -> None:
        frete_cep_origem.value = ""
        frete_cep_destino.value = ""
        frete_altura.value = "10"
        frete_largura.value = "11"
        frete_comprimento.value = "17"
        frete_peso.value = "300"
        frete_formato.value = "1"
        frete_tipo_servico.value = "40010"
        frete_aviso_recebimento.value = False
        frete_mao_propria.value = False
        forcar_api_frete.value = False
        limpar_resultado(resultado_frete)
        barra_status.limpar()
        page.run_task(focar_pesquisa, 3)
        page.update()

    btn_frete = ft.FilledButton(
        "Calcular frete", icon=ft.Icons.LOCAL_SHIPPING, on_click=buscar_frete
    )
    btn_limpar_frete = ft.OutlinedButton(
        "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar_frete
    )
    frete_cep_destino.on_submit = buscar_frete

    painel_frete = criar_painel_duplo(
        "Frete — pesquisa",
        ft.Column(
            [
                ft.Row([frete_cep_origem, frete_cep_destino], spacing=8, wrap=True),
                ft.Row(
                    [frete_altura, frete_largura, frete_comprimento, frete_peso],
                    spacing=8,
                    wrap=True,
                ),
                ft.Row([frete_formato, frete_tipo_servico], spacing=8, wrap=True),
                ft.Text(
                    "WSFRETEJ — cálculo de frete (timeout até 450s)",
                    size=11,
                    color=ft.Colors.GREY_700,
                ),
                frete_aviso_recebimento,
                frete_mao_propria,
                forcar_api_frete,
                linha_botoes_acao(btn_frete, btn_limpar_frete),
            ],
            spacing=8,
            tight=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        "Frete — retorno",
        resultado_frete,
    )
    campos_pesquisa.append(frete_cep_origem)

    rastreio_codigo = ft.TextField(
        label="Código de rastreamento",
        hint_text="Ex.: AA123456789BR (Enter)",
        width=largura_campo,
        max_length=20,
        dense=True,
    )
    forcar_api_rastreio = ft.Checkbox(label="Forçar API (ignorar cache)", value=False)
    resultado_rastreio = ft.Column(
        spacing=6,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[mensagem_resultado_vazio()],
    )

    def exibir_rastreio(payload: dict, source: str) -> None:
        resultado_rastreio.controls = montar_painel_resultado(
            page, payload, tipo="correios_rastreio"
        )
        barra_status.atualizar(payload, source)

    async def buscar_rastreio(_: ft.ControlEvent) -> None:
        btn_rastreio.disabled = True
        page.update()
        try:
            resposta = await asyncio.to_thread(
                service_correios.rastrear,
                rastreio_codigo.value or "",
                forcar_api=forcar_api_rastreio.value,
            )
            exibir_rastreio(resposta["data"], resposta["source"])
            barra_status.atualizar_totais(db.get_consumed_totals())
        finally:
            btn_rastreio.disabled = False
            page.update()

    def limpar_rastreio(_: ft.ControlEvent) -> None:
        rastreio_codigo.value = ""
        forcar_api_rastreio.value = False
        limpar_resultado(resultado_rastreio)
        barra_status.limpar()
        page.run_task(focar_pesquisa, 3)
        page.update()

    btn_rastreio = ft.FilledButton(
        "Rastrear", icon=ft.Icons.TRACK_CHANGES, on_click=buscar_rastreio
    )
    btn_limpar_rastreio = ft.OutlinedButton(
        "Limpar", icon=ft.Icons.CLEAR_ALL, on_click=limpar_rastreio
    )
    rastreio_codigo.on_submit = buscar_rastreio

    painel_rastreio = criar_painel_duplo(
        "Rastreio — pesquisa",
        ft.Column(
            [
                rastreio_codigo,
                ft.Text(
                    "WSRASTREIOJ — rastreamento de objeto",
                    size=11,
                    color=ft.Colors.GREY_700,
                ),
                forcar_api_rastreio,
                linha_botoes_acao(btn_rastreio, btn_limpar_rastreio),
            ],
            spacing=8,
            tight=True,
        ),
        "Rastreio — retorno",
        resultado_rastreio,
    )

    painel_correios = ft.Column(
        [
            painel_frete,
            ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
            painel_rastreio,
        ],
        spacing=8,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

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
                        painel_correios,
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
