#!/usr/bin/env bash
# Instala dependências de desenvolvimento (pytest, pylint, mypy, cobertura).
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v uv >/dev/null 2>&1; then
  echo "[uv] Sincronizando grupo dev..."
  uv sync --group dev
else
  echo "[pip] Instalando requirements-dev.txt..."
  python -m pip install -r requirements-dev.txt
fi

echo
echo "Ferramentas disponíveis:"
echo "  uv run pytest"
echo "  uv run pytest --cov=app --cov-report=term-missing"
echo "  uv run pylint app main.py"
echo "  uv run mypy"
