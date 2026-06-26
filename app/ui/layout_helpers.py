"""Layout compartilhado: frames e barra de status."""

import flet as ft


def criar_frame(titulo: str, conteudo: ft.Control, *, expand: bool = False) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(titulo, size=13, weight=ft.FontWeight.W_600),
                ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                conteudo,
            ],
            spacing=6,
            expand=expand,
        ),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        padding=10,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        expand=expand,
    )


def criar_painel_duplo(
    titulo_esq: str,
    conteudo_esq: ft.Control,
    titulo_dir: str,
    conteudo_dir: ft.Control,
    *,
    expand: bool = True,
) -> ft.Row:
    return ft.Row(
        [
            criar_frame(titulo_esq, conteudo_esq, expand=expand),
            criar_frame(titulo_dir, conteudo_dir, expand=expand),
        ],
        spacing=10,
        expand=expand,
        vertical_alignment=ft.CrossAxisAlignment.START if not expand else ft.CrossAxisAlignment.STRETCH,
    )


def mensagem_resultado_vazio() -> ft.Text:
    return ft.Text(
        "Nenhum resultado exibido.",
        size=13,
        color=ft.Colors.GREY_600,
        italic=True,
    )


def linha_botoes_acao(
    btn_consultar: ft.Control,
    btn_limpar: ft.Control,
) -> ft.Row:
    return ft.Row(
        [btn_consultar, btn_limpar],
        spacing=8,
        wrap=True,
    )


class BarraStatus:
    """Linha de status fixa no rodapé (status, return, consumed)."""

    def __init__(self) -> None:
        self.status_txt = ft.Text("status: —", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.return_txt = ft.Text("return: —", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.consumed_txt = ft.Text("consumed: —", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.origem_txt = ft.Text("origem: —", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.message_txt = ft.Text(
            "message: —",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=True,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.totais_txt = ft.Text("", size=11, color=ft.Colors.BLUE_GREY_700)

    def atualizar(self, payload: dict, source: str) -> None:
        creditos = 0 if source == "local" else int(payload.get("consumed") or 0)
        status = payload.get("status", "—")
        self.status_txt.value = f"status: {status}"
        self.return_txt.value = f"return: {payload.get('return', '—')}"
        self.consumed_txt.value = f"consumed: {creditos}"
        self.origem_txt.value = f"origem: {source}"
        self.message_txt.value = f"message: {payload.get('message') or '—'}"

    def atualizar_totais(self, totais: dict[str, int]) -> None:
        self.totais_txt.value = (
            f"Totais API — CPF {totais['cpf']} | CNPJ {totais['cnpj']} | "
            f"CEP {totais['cep']} | Correios {totais['correios']} | Outros {totais['outros']}"
        )

    def limpar(self) -> None:
        self.status_txt.value = "status: —"
        self.return_txt.value = "return: —"
        self.consumed_txt.value = "consumed: —"
        self.origem_txt.value = "origem: —"
        self.message_txt.value = "message: —"

    def control(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self.status_txt,
                            ft.VerticalDivider(width=1),
                            self.return_txt,
                            ft.VerticalDivider(width=1),
                            self.consumed_txt,
                            ft.VerticalDivider(width=1),
                            self.origem_txt,
                            ft.VerticalDivider(width=1),
                            self.message_txt,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self.totais_txt,
                ],
                spacing=4,
            ),
            border=ft.Border.only(top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        )
