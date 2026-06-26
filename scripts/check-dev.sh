#!/usr/bin/env bash
# Executa testes, cobertura, pylint e mypy (requer grupo dev instalado).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== pytest ==="
uv run pytest --cov=app --cov-report=term-missing

echo
echo "=== pylint ==="
uv run pylint app main.py

echo
echo "=== mypy ==="
uv run mypy

echo
echo "Verificação de desenvolvimento concluída com sucesso."
