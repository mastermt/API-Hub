"""Cópia para área de transferência (Flet async + fallback Windows/desktop)."""

import subprocess
import sys

import flet as ft


def _copiar_fallback(texto: str) -> bool:
    """Fallback quando o Clipboard do Flet falha (comum no desktop Windows)."""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["clip"],
                input=texto.encode("utf-16le"),
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return True
        except Exception:
            pass

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(texto)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


async def copiar_texto(page: ft.Page, texto: str) -> bool:
    try:
        await page.clipboard.set(texto)
        return True
    except Exception:
        return _copiar_fallback(texto)


def mostrar_feedback_copia(page: ft.Page, label: str, sucesso: bool) -> None:
    if sucesso:
        msg = f"{label} copiado para a área de transferência."
    else:
        msg = f"Não foi possível copiar {label}."
    page.show_dialog(ft.SnackBar(ft.Text(msg)))
