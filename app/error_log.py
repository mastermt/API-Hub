"""Redireciona erros e stderr para arquivo de log."""

from __future__ import annotations

import logging
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import TextIO

from app.config import BASE_DIR, is_compiled_build


class _TeeStream(TextIO):
    def __init__(self, log_file: TextIO, original: TextIO | None) -> None:
        self._log_file = log_file
        self._original = original

    def write(self, data: str) -> int:
        if not data:
            return 0
        self._log_file.write(data)
        self._log_file.flush()
        if self._original is not None:
            self._original.write(data)
            self._original.flush()
        return len(data)

    def flush(self) -> None:
        self._log_file.flush()
        if self._original is not None:
            self._original.flush()


def _default_log_path() -> Path:
    from os import getenv

    configured = getenv("ERROR_LOG_PATH", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path

    return BASE_DIR / "logs" / "erros.log"


def install_error_log() -> Path:
    log_path = _default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = log_path.open("a", encoding="utf-8", buffering=1)
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    log_file.write(f"\n--- Inicio {started_at} ---\n")
    log_file.flush()

    original_stderr = sys.stderr
    sys.stderr = _TeeStream(log_file, original_stderr if not is_compiled_build() else None)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
        force=True,
    )

    def _log_exception(exc_type, exc_value, exc_tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            if original_stderr is not None:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        message = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log_file.write(message)
        log_file.flush()
        logging.getLogger(__name__).error("Excecao nao tratada:\n%s", message)
        if original_stderr is not None and not is_compiled_build():
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _log_exception

    if hasattr(threading, "excepthook"):

        def _thread_exception(args: threading.ExceptHookArgs) -> None:
            message = "".join(
                traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)
            )
            log_file.write(message)
            log_file.flush()
            logging.getLogger(__name__).error("Excecao em thread:\n%s", message)

        threading.excepthook = _thread_exception

    return log_path
