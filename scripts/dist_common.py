"""Funções compartilhadas para pós-build Nuitka (Windows e Linux)."""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

_STDLIB_PACKAGES = ("ctypes", "sqlite3")

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

_CONDA_RUNTIME_DLLS = (
    "ffi.dll",
    "ffi-7.dll",
    "ffi-8.dll",
    "libcrypto-3-x64.dll",
    "libssl-3-x64.dll",
    "sqlite3.dll",
)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def python_base_dir() -> Path:
    return Path(getattr(sys, "base_prefix", sys.prefix))


def stdlib_lib_dir() -> Path:
    base = python_base_dir()
    versioned = base / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    if versioned.is_dir():
        return versioned
    return base / "Lib"


def copy_stdlib_package(dist_dir: Path) -> None:
    lib_dir = stdlib_lib_dir()
    for package_name in _STDLIB_PACKAGES:
        source = lib_dir / package_name
        if not source.is_dir():
            continue
        target = dist_dir / package_name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        print(f"Pacote: {package_name} -> {target}")


def copy_stdlib_extension(dist_dir: Path, module_name: str) -> None:
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return

    module_file = getattr(module, "__file__", None)
    if not module_file:
        return

    source = Path(module_file).resolve()
    if source.suffix.lower() not in {".pyd", ".so"}:
        return

    target = dist_dir / source.name
    shutil.copy2(source, target)
    print(f"Runtime: {source.name} -> {target}")


def copy_stdlib_extensions(dist_dir: Path) -> None:
    for module_name in _STDLIB_EXTENSIONS:
        copy_stdlib_extension(dist_dir, module_name)


def copy_conda_runtime_dlls(dist_dir: Path) -> None:
    bin_dir = python_base_dir() / "Library" / "bin"
    if not bin_dir.is_dir():
        return

    for name in _CONDA_RUNTIME_DLLS:
        source = bin_dir / name
        if source.is_file():
            shutil.copy2(source, dist_dir / name)
            print(f"Runtime: {name} -> {dist_dir / name}")


def copy_missing_python_dlls(dist_dir: Path) -> None:
    dlls_dir = python_base_dir() / "DLLs"
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


def copy_missing_lib_dynload(dist_dir: Path) -> None:
    dynload = stdlib_lib_dir() / "lib-dynload"
    if not dynload.is_dir():
        return

    existing = {path.name for path in dist_dir.iterdir() if path.is_file()}
    for item in dynload.iterdir():
        if item.suffix != ".so" or item.name.startswith("_test"):
            continue
        if item.name in existing:
            continue
        shutil.copy2(item, dist_dir / item.name)
        print(f"Runtime: {item.name} -> {dist_dir / item.name}")


def copy_package_data(dist_dir: Path, package_name: str, extensions: set[str]) -> None:
    try:
        module = importlib.import_module(package_name)
    except ImportError:
        return

    source_root = Path(module.__file__).resolve().parent
    target_root = dist_dir / package_name
    for path in source_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        relative = path.relative_to(source_root)
        target = target_root / relative
        if target.is_file():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        print(f"{package_name}: {relative} -> {target}")


def copy_flet_package_data(dist_dir: Path) -> None:
    copy_package_data(
        dist_dir,
        "flet",
        {".json", ".ttf", ".woff", ".woff2", ".png"},
    )


def copy_flet_web_package_data(dist_dir: Path) -> None:
    copy_package_data(
        dist_dir,
        "flet_web",
        {
            ".json",
            ".js",
            ".mjs",
            ".css",
            ".html",
            ".wasm",
            ".ttf",
            ".woff",
            ".woff2",
            ".png",
            ".svg",
            ".ico",
            ".map",
        },
    )


def copy_app_data(dist_dir: Path, root: Path) -> None:
    data_dir = dist_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_src = root / "data" / "consultas.db"
    if db_src.is_file():
        shutil.copy2(db_src, data_dir / "consultas.db")
        print(f"Dados: {db_src} -> {data_dir / 'consultas.db'}")

    env_src = root / ".env"
    env_dst = dist_dir / ".env"
    if env_src.is_file():
        shutil.copy2(env_src, env_dst)
        print(f"Config: {env_src} -> {env_dst}")
    elif not env_dst.is_file():
        example = root / ".env.example"
        if example.is_file():
            shutil.copy2(example, env_dst)
            print(f"Config: {example} -> {env_dst}")


def validate_dist_dir(dist_dir: Path, root: Path, *, require_exe: bool) -> None:
    dist_dir = dist_dir.resolve()
    root = root.resolve()

    if dist_dir == root:
        raise SystemExit(
            "ERRO: destino invalido (raiz do projeto). "
            "Informe build/.../main.dist"
        )
    if (dist_dir / "pyproject.toml").is_file():
        raise SystemExit("ERRO: destino parece ser o codigo-fonte, nao o main.dist.")
    if not dist_dir.name.endswith(".dist"):
        raise SystemExit(
            f"ERRO: destino deve ser uma pasta '*.dist', recebido: {dist_dir.name}"
        )
    if "build" not in dist_dir.parts:
        raise SystemExit(f"ERRO: destino deve ficar dentro de 'build/', recebido: {dist_dir}")

    if require_exe:
        if not any(dist_dir.glob("*.exe")):
            raise SystemExit("ERRO: nenhum .exe encontrado no main.dist.")
    elif not (dist_dir / "api-consulta").is_file():
        raise SystemExit("ERRO: binario api-consulta nao encontrado no main.dist.")
