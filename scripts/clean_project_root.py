"""Remove artefatos de build copiados por engano para a raiz do projeto."""

from __future__ import annotations

import shutil
from pathlib import Path

_STDLIB_DIRS = ("ctypes", "sqlite3", "flet")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    removed: list[str] = []

    for name in _STDLIB_DIRS:
        path = root / name
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(f"{name}/")

    for path in root.glob("*.pyd"):
        path.unlink()
        removed.append(path.name)

    for path in root.glob("*.so"):
        path.unlink()
        removed.append(path.name)

    for path in root.glob("*.dll"):
        if path.name.lower() in {
            "ffi.dll",
            "ffi-7.dll",
            "ffi-8.dll",
            "libcrypto-3-x64.dll",
            "libssl-3-x64.dll",
            "sqlite3.dll",
            "python314.dll",
            "vcruntime140.dll",
            "vcruntime140_1.dll",
            "zlib.dll",
        }:
            path.unlink()
            removed.append(path.name)

    if removed:
        print("Removido da raiz do projeto:", ", ".join(removed))
    else:
        print("Raiz do projeto limpa (nada a remover).")


if __name__ == "__main__":
    main()
