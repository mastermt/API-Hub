"""Prepara main.dist após compilação Nuitka (Windows desktop ou Linux web)."""

from __future__ import annotations

import argparse
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


def _python_base_dir() -> Path:
    return Path(getattr(sys, "base_prefix", sys.prefix))


def _stdlib_lib_dir() -> Path:
    base = _python_base_dir()
    versioned = base / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    if versioned.is_dir():
        return versioned
    return base / "Lib"


def _copy_stdlib_package(dist_dir: Path) -> None:
    lib_dir = _stdlib_lib_dir()
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


def _copy_stdlib_extension(dist_dir: Path, module_name: str) -> None:
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return

    source = Path(module.__file__).resolve()
    if source.suffix.lower() not in {".pyd", ".so"}:
        return

    target = dist_dir / source.name
    shutil.copy2(source, target)
    print(f"Runtime: {source.name} -> {target}")


def _copy_conda_runtime_dlls(dist_dir: Path) -> None:
    bin_dir = _python_base_dir() / "Library" / "bin"
    if not bin_dir.is_dir():
        return

    for name in _CONDA_RUNTIME_DLLS:
        source = bin_dir / name
        if source.is_file():
            shutil.copy2(source, dist_dir / name)
            print(f"Runtime: {name} -> {dist_dir / name}")


def _copy_missing_python_dlls(dist_dir: Path) -> None:
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


def _copy_missing_lib_dynload(dist_dir: Path) -> None:
    dynload = _stdlib_lib_dir() / "lib-dynload"
    if not dynload.is_dir():
        return

    existing = {path.name for path in dist_dir.iterdir() if path.is_file()}
    for item in dynload.iterdir():
        if item.suffix != ".so" or item.name.startswith(("_test",)):
            continue
        if item.name in existing:
            continue
        shutil.copy2(item, dist_dir / item.name)
        print(f"Runtime: {item.name} -> {dist_dir / item.name}")


def _copy_package_data(dist_dir: Path, package_name: str, extensions: set[str]) -> None:
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


def _copy_flet_package_data(dist_dir: Path) -> None:
    _copy_package_data(
        dist_dir,
        "flet",
        {".json", ".ttf", ".woff", ".woff2", ".png"},
    )


def _copy_flet_web_package_data(dist_dir: Path) -> None:
    _copy_package_data(
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


def _validate_dist_dir(dist_dir: Path, project_root: Path, profile: str) -> None:
    dist_dir = dist_dir.resolve()
    project_root = project_root.resolve()

    if dist_dir == project_root:
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

    if profile == "linux-web":
        if not (dist_dir / "api-consulta").is_file():
            raise SystemExit("ERRO: binario api-consulta nao encontrado no main.dist.")
    else:
        if not any(dist_dir.glob("*.exe")):
            raise SystemExit("ERRO: nenhum .exe encontrado no main.dist.")


def _write_web_marker(dist_dir: Path) -> None:
    marker = dist_dir / ".web-dist"
    marker.write_text("linux-web\n", encoding="utf-8")
    print(f"Marcador: {marker}")


def _prepare_windows_desktop(dist_dir: Path, project_root: Path) -> None:
    _copy_stdlib_package(dist_dir)
    for module_name in _STDLIB_EXTENSIONS:
        _copy_stdlib_extension(dist_dir, module_name)
    _copy_conda_runtime_dlls(dist_dir)
    _copy_missing_python_dlls(dist_dir)
    _copy_flet_package_data(dist_dir)
    _copy_app_data(dist_dir, project_root)


def _prepare_linux_web(dist_dir: Path, project_root: Path) -> None:
    _copy_stdlib_package(dist_dir)
    for module_name in _STDLIB_EXTENSIONS:
        _copy_stdlib_extension(dist_dir, module_name)
    _copy_missing_lib_dynload(dist_dir)
    _copy_flet_package_data(dist_dir)
    _copy_flet_web_package_data(dist_dir)
    _copy_app_data(dist_dir, project_root)
    _write_web_marker(dist_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara pasta main.dist após Nuitka.")
    parser.add_argument(
        "dist_dir",
        nargs="?",
        default="",
        help="Caminho para build/.../main.dist",
    )
    parser.add_argument(
        "--profile",
        choices=("windows-desktop", "linux-web"),
        default="windows-desktop",
        help="Perfil de distribuicao (padrao: windows-desktop)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    if args.dist_dir.strip():
        dist_dir = Path(args.dist_dir)
    elif args.profile == "linux-web":
        dist_dir = project_root / "build" / "linux-web" / "main.dist"
    else:
        dist_dir = project_root / "build" / "nuitka-zig" / "main.dist"

    if not dist_dir.is_dir():
        raise SystemExit(f"Pasta de distribuicao nao encontrada: {dist_dir}")

    _validate_dist_dir(dist_dir, project_root, args.profile)

    if args.profile == "linux-web":
        _prepare_linux_web(dist_dir, project_root)
    else:
        _prepare_windows_desktop(dist_dir, project_root)

    print(f"Distribuicao pronta em: {dist_dir}")


if __name__ == "__main__":
    main()
