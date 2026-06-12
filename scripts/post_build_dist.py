"""Prepara main.dist após compilação Nuitka (runtime Python, .env, banco)."""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

# Pacotes stdlib que o Nuitka pode omitir com compilação parcial.
_STDLIB_PACKAGES = (
    "ctypes",
    "sqlite3",
)


def _python_base_dir() -> Path:
    return Path(getattr(sys, "base_prefix", sys.prefix))

# Extensões nativas frequentemente omitidas quando o Nuitka usa --include-package.
_STDLIB_EXTENSIONS = (
    "_ctypes",
    "_sqlite3",
    "_socket",
    "_ssl",
    "_hashlib",
    "_queue",
    "_multiprocessing",
    "pyexpat",
    "select",
    "unicodedata",
)


def _copy_stdlib_package(dist_dir: Path, package_name: str) -> None:
    source = _python_base_dir() / "Lib" / package_name
    target = dist_dir / package_name
    if not source.is_dir() or target.exists():
        return

    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    print(f"Pacote: {package_name} -> {target}")


def _copy_stdlib_extension(dist_dir: Path, module_name: str) -> None:
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return

    source = Path(module.__file__).resolve()
    if source.suffix.lower() != ".pyd":
        return

    target = dist_dir / source.name
    if target.exists():
        return

    shutil.copy2(source, target)
    print(f"Runtime: {source.name} -> {target}")


def _copy_dlls_folder(dist_dir: Path) -> None:
    dlls_dir = _python_base_dir() / "DLLs"
    if not dlls_dir.is_dir():
        return

    existing = {path.name.lower() for path in dist_dir.iterdir() if path.is_file()}
    for item in dlls_dir.iterdir():
        if item.suffix.lower() not in {".pyd", ".dll"}:
            continue
        if item.name.startswith(("_test", "xxlimited")):
            continue
        if item.name.lower() in existing:
            continue
        shutil.copy2(item, dist_dir / item.name)
        print(f"Runtime: {item.name} -> {dist_dir / item.name}")


def _copy_app_data(dist_dir: Path, project_root: Path) -> None:
    data_dir = dist_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_src = project_root / "data" / "consultas.db"
    if db_src.is_file():
        shutil.copy2(db_src, data_dir / "consultas.db")
        print(f"Dados: {db_src} -> {data_dir / 'consultas.db'}")

    env_src = project_root / ".env"
    env_dst = dist_dir / ".env"
    if env_src.is_file():
        shutil.copy2(env_src, env_dst)
        print(f"Config: {env_src} -> {env_dst}")
    elif not env_dst.is_file():
        example = project_root / ".env.example"
        if example.is_file():
            shutil.copy2(example, env_dst)
            print(f"Config: {example} -> {env_dst}")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    dist_dir = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else project_root / "build" / "nuitka-zig" / "main.dist"
    )

    if not dist_dir.is_dir():
        raise SystemExit(f"Pasta de distribuicao nao encontrada: {dist_dir}")

    for package_name in _STDLIB_PACKAGES:
        _copy_stdlib_package(dist_dir, package_name)

    for module_name in _STDLIB_EXTENSIONS:
        _copy_stdlib_extension(dist_dir, module_name)

    _copy_dlls_folder(dist_dir)
    _copy_app_data(dist_dir, project_root)
    print(f"Distribuicao pronta em: {dist_dir}")


if __name__ == "__main__":
    main()
