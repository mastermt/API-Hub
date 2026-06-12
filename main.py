"""Ponto de entrada da aplicação Flet."""

import argparse
import signal
import sys

import flet as ft

from app.ui.app import build_app


def _install_signal_handlers() -> None:
    """Garante que Ctrl+C (e Ctrl+Break no Windows) encerre o processo."""

    def _handler(signum: int, frame) -> None:
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _handler)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="API Consulta - Hub do Desenvolvedor")
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Abre como app desktop (padrão: navegador web)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor web")
    parser.add_argument("--port", type=int, default=8550, help="Porta do servidor web")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    _install_signal_handlers()

    try:
        if args.desktop:
            ft.run(main=build_app)
        else:
            ft.run(
                main=build_app,
                view=ft.AppView.WEB_BROWSER,
                host=args.host,
                port=args.port,
            )
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main()
