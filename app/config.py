import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def dist_root() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.argv[0]).resolve().parent

    candidate = Path(sys.argv[0]).resolve()
    if not candidate.is_file():
        return None

    root = candidate.parent
    if (root / "pyproject.toml").exists():
        return None

    if candidate.suffix.lower() == ".exe":
        if any(root.glob("python3*.dll")) or (root / "app").is_dir():
            return root
        return None

    if any(root.glob("libpython*.so*")):
        return root

    return None


def is_compiled_build() -> bool:
    return dist_root() is not None


def is_compiled_web_dist() -> bool:
    root = dist_root()
    return root is not None and (root / ".web-dist").is_file()


def _resolve_base_dir() -> Path:
    root = dist_root()
    if root is not None:
        return root

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

CORREIOS_API_TIMEOUT = 450
