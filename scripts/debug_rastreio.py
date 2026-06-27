"""Debug temporário: testa variantes da API de rastreio Hub (usa .env)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

token = os.getenv("HUB_TOKEN", "").strip()
if not token:
    raise SystemExit("HUB_TOKEN não configurado no .env")

codigos = sys.argv[1:] or ["AP018100208BR", "AP136189765BR"]
base = "https://ws.hubdodesenvolvedor.com.br/v2/correios/"

variantes = [
    lambda c: {"servico": "rastreamento", "codigo_rastreamento": c, "token": token},
    lambda c: {"servico": "rastreamento", "codigo_rastreamento": c, "tipo": "L", "token": token},
    lambda c: {"servico": "rastreamento", "codigo_rastreamento": c, "resultado": "T", "token": token},
    lambda c: {
        "servico": "rastreamento",
        "codigo_rastreamento": c,
        "tipo": "L",
        "resultado": "T",
        "token": token,
    },
    lambda c: {"servico": "rastreamento", "codigo": c, "token": token},
    lambda c: {"servico": "rastreio", "codigo_rastreamento": c, "token": token},
]

for codigo in codigos:
    print(f"\n######## {codigo} ########")
    for idx, build in enumerate(variantes, 1):
        params = build(codigo)
        public = {k: v for k, v in params.items() if k != "token"}
        r = httpx.get(base, params=params, timeout=120, follow_redirects=True)
        print(f"\n--- variante {idx} {public} HTTP {r.status_code}")
        try:
            body = r.json()
            print(json.dumps(body, ensure_ascii=False, indent=2)[:1500])
        except Exception:
            print(r.text[:500])
