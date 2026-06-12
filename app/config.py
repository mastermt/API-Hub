import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def is_compiled_build() -> bool:
    if getattr(sys, "frozen", False):
        return True

    exe = Path(sys.argv[0]).resolve()
    if exe.suffix.lower() != ".exe" or not exe.is_file():
        return False

    dist_root = exe.parent
    if (dist_root / "pyproject.toml").exists():
        return False

    # Nuitka standalone: python3xx.dll ao lado do .exe (app fica embutido, sem pasta app/)
    if any(dist_root.glob("python3*.dll")):
        return True

    return (dist_root / "app").is_dir()


def _resolve_base_dir() -> Path:
    if is_compiled_build():
        return Path(sys.argv[0]).resolve().parent

    return Path(__file__).resolve().parent.parent


BASE_DIR = _resolve_base_dir()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

_db_path = os.getenv("DB_PATH", "").strip()
if _db_path:
    DB_PATH = Path(_db_path)
    if not DB_PATH.is_absolute():
        DB_PATH = BASE_DIR / DB_PATH
else:
    DB_PATH = DATA_DIR / "consultas.db"

HUB_BASE_URL = "https://ws.hubdodesenvolvedor.com.br/v2"
HUB_TOKEN = os.getenv("HUB_TOKEN", "")

CPF_API_TIMEOUT = 600  # normal
CPF_API_TIMEOUT_TURBO = 30
CPF_CONNECT_TIMEOUT = 10

CNPJ_API_TIMEOUT = 300
CNPJ_API_TIMEOUT_IE_ONLINE = 360  # +60s quando ie=1
