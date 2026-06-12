"""Garante flet-desktop e o arquivo flet-windows.zip para compilação Nuitka."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from flet.utils.pip import ensure_flet_desktop_package_installed


def main() -> None:
    ensure_flet_desktop_package_installed()

    import flet_desktop
    from flet_desktop import get_artifact_filename, get_package_bin_dir

    dest_dir = Path(get_package_bin_dir())
    dest_dir.mkdir(parents=True, exist_ok=True)

    artifact = get_artifact_filename()
    dest = dest_dir / artifact
    if dest.is_file():
        print(f"Arquivo do cliente Flet OK: {dest}")
        return

    version = flet_desktop.version.version
    url = f"https://github.com/flet-dev/flet/releases/download/v{version}/{artifact}"
    print(f"Baixando {url} ...")
    urllib.request.urlretrieve(url, dest)
    print(f"Salvo em {dest}")


if __name__ == "__main__":
    main()
