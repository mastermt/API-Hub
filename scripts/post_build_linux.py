"""Prepara main.dist após compilação Nuitka no Linux (modo web)."""

from __future__ import annotations

import argparse
import stat
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from dist_common import (
    copy_app_data,
    copy_flet_package_data,
    copy_flet_web_package_data,
    copy_missing_lib_dynload,
    copy_stdlib_extensions,
    copy_stdlib_package,
    project_root,
    validate_dist_dir,
)

DEFAULT_DIST = "build/linux-web/main.dist"
APP_BINARY = "api-consulta"


def _write_web_marker(dist_dir: Path) -> None:
    marker = dist_dir / ".web-dist"
    marker.write_text("linux-web\n", encoding="utf-8")
    print(f"Marcador: {marker}")


def _ensure_executable(dist_dir: Path) -> None:
    binary = dist_dir / APP_BINARY
    if not binary.is_file():
        return
    mode = binary.stat().st_mode
    binary.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Permissao: {binary} (+x)")


def prepare_linux_web_dist(dist_dir: Path, root: Path) -> None:
    copy_stdlib_package(dist_dir)
    copy_stdlib_extensions(dist_dir)
    copy_missing_lib_dynload(dist_dir)
    copy_flet_package_data(dist_dir)
    copy_flet_web_package_data(dist_dir)
    copy_app_data(dist_dir, root)
    _write_web_marker(dist_dir)
    _ensure_executable(dist_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara pasta main.dist Linux (modo web) após Nuitka.",
    )
    parser.add_argument(
        "dist_dir",
        nargs="?",
        default="",
        help=f"Caminho para main.dist (padrao: {DEFAULT_DIST})",
    )
    args = parser.parse_args()

    root = project_root()
    dist_dir = Path(args.dist_dir) if args.dist_dir.strip() else root / DEFAULT_DIST

    if not dist_dir.is_dir():
        raise SystemExit(f"Pasta de distribuicao nao encontrada: {dist_dir}")

    validate_dist_dir(dist_dir, root, require_exe=False)
    prepare_linux_web_dist(dist_dir, root)
    print(f"Distribuicao Linux pronta em: {dist_dir}")


if __name__ == "__main__":
    main()
