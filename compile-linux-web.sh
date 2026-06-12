#!/usr/bin/env bash
# Compila distribuição Linux (modo web) com Nuitka.
# Execute em Linux ou WSL — Nuitka não faz cross-compile a partir do Windows.
set -euo pipefail

cd "$(dirname "$0")"

BUILD_DIR="build/linux-web"
DIST_DIR="${BUILD_DIR}/main.dist"
APP_NAME="api-consulta"
MODE="standalone"

if [[ "${1:-}" == "onefile" ]]; then
  MODE="onefile"
fi

echo
echo "=== API Consulta CPF - Nuitka Linux Web (${MODE}) ==="
echo "Saida: ${BUILD_DIR}"
echo

command -v uv >/dev/null 2>&1 || {
  echo "[ERRO] uv nao encontrado no PATH."
  echo "Instale em https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
}

echo "[1/4] Limpando artefatos na raiz do projeto..."
uv run python scripts/clean_project_root.py

echo
echo "[2/4] Sincronizando dependencias (flet-web)..."
uv sync --group build-linux-web

APP_VERSION="$(uv run python -c "import tomllib; v=tomllib.load(open('pyproject.toml','rb'))['project']['version'].split('.'); v+=['0']*(4-len(v)); print('.'.join(v[:4]))")"
echo "Versao: ${APP_VERSION}"

echo
echo "[3/4] Criando pasta de saida..."
mkdir -p "${BUILD_DIR}"

NUITKA_ARGS=(
  --assume-yes-for-downloads
  "--output-dir=${BUILD_DIR}"
  "--mode=${MODE}"
  "--output-filename=${APP_NAME}"
  --include-package=app
  --include-package=flet
  --include-package=flet_web
  --include-package=httpx
  --include-package=httpx._transports
  --include-package=anyio
  --include-package=certifi
  --include-package=dotenv
  --include-package=msgpack
  --include-package=oauthlib
  --include-package=repath
  --include-package=uvicorn
  --include-package=starlette
  --include-module=ctypes
  --include-module=_ctypes
  --include-module=sqlite3
  --include-module=_sqlite3
  --include-package-data=flet
  --include-package-data=flet_web
  --include-data-dir=assets=assets
  --product-name="API Consulta CPF"
  --file-description="Consultas CPF, CNPJ e CEP - Hub do Desenvolvedor"
  --company-name="Paitom TIC"
  "--file-version=${APP_VERSION}"
  "--product-version=${APP_VERSION}"
  main.py
)

if command -v zig >/dev/null 2>&1; then
  echo "[4/4] Compilando com Nuitka (--zig)..."
  NUITKA_ARGS=(--zig "${NUITKA_ARGS[@]}")
else
  echo "[4/4] Compilando com Nuitka (zig nao encontrado, usando compilador padrao)..."
fi

uv run python -m nuitka "${NUITKA_ARGS[@]}"

echo
echo "Compilacao concluida em ${BUILD_DIR}"

if [[ "${MODE}" == "standalone" ]]; then
  echo "Executavel: ${DIST_DIR}/${APP_NAME}"
  uv run python scripts/post_build_dist.py "${DIST_DIR}" --profile linux-web
  echo
  echo "Distribuicao web pronta. Copie a pasta main.dist para o servidor Linux."
  echo "Uso: ./${APP_NAME} --host 0.0.0.0 --port 8550"
else
  echo "Executavel: ${BUILD_DIR}/${APP_NAME}.bin"
fi
