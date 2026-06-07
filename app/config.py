import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "consultas.db"))

HUB_BASE_URL = "https://ws.hubdodesenvolvedor.com.br/v2"
HUB_TOKEN = os.getenv("HUB_TOKEN", "")

CPF_API_TIMEOUT = 600  # normal
CPF_API_TIMEOUT_TURBO = 30
CPF_CONNECT_TIMEOUT = 10

CNPJ_API_TIMEOUT = 300
CNPJ_API_TIMEOUT_IE_ONLINE = 360  # +60s quando ie=1
