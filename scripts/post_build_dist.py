"""Prepara main.dist após compilação Nuitka no Windows (modo desktop)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from dist_common import (
    copy_app_data,
    copy_conda_runtime_dlls,
    copy_flet_package_data,
    copy_missing_python_dlls,
    copy_stdlib_extensions,
    copy_stdlib_package,
    project_root,
    validate_dist_dir,
)

DEFAULT_DIST = "build/nuitka-zig/main.dist"


def prepare_windows_desktop_dist(dist_dir: Path, root: Path) -> None:
    copy_stdlib_package(dist_dir)
    copy_stdlib_extensions(dist_dir)
    copy_conda_runtime_dlls(dist_dir)
    copy_missing_python_dlls(dist_dir)
    copy_flet_package_data(dist_dir)
    copy_app_data(dist_dir, root)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara pasta main.dist Windows (modo desktop) após Nuitka.",
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

    validate_dist_dir(dist_dir, root, require_exe=True)
    prepare_windows_desktop_dist(dist_dir, root)
    print(f"Distribuicao Windows pronta em: {dist_dir}")


if __name__ == "__main__":
    main()
