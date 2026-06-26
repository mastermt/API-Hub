#!/usr/bin/env bash
# Instala a distribuicao Linux (main.dist) em /srv e registra servico systemd.
set -euo pipefail

INSTALL_DIR="/srv/api-consulta-cpf"
SERVICE_NAME="api-consulta-cpf"
SERVICE_USER="api-consulta"
SERVICE_PORT="${SERVICE_PORT:-8550}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo "Uso: sudo $0 /caminho/para/build/linux-web/main.dist"
  echo
  echo "Variaveis opcionais:"
  echo "  SERVICE_PORT=8550   Porta HTTP do Flet"
  echo "  INSTALL_DIR=...     Padrao: /srv/api-consulta-cpf"
  exit 1
}

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[ERRO] Execute como root (sudo)."
  usage
fi

DIST_SRC="${1:-}"
if [[ -z "${DIST_SRC}" || ! -d "${DIST_SRC}" ]]; then
  echo "[ERRO] Informe o caminho da pasta main.dist compilada."
  usage
fi

DIST_SRC="$(cd "${DIST_SRC}" && pwd)"

if [[ ! -f "${DIST_SRC}/api-consulta" ]]; then
  echo "[ERRO] Binario api-consulta nao encontrado em: ${DIST_SRC}"
  exit 1
fi

if ! id "${SERVICE_USER}" &>/dev/null; then
  echo "Criando usuario de sistema: ${SERVICE_USER}"
  useradd --system --home "${INSTALL_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
  echo "Parando servico ${SERVICE_NAME}..."
  systemctl stop "${SERVICE_NAME}"
fi

echo "Instalando em ${INSTALL_DIR}..."
mkdir -p "${INSTALL_DIR}"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "${DIST_SRC}/" "${INSTALL_DIR}/"
else
  find "${INSTALL_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "${DIST_SRC}/." "${INSTALL_DIR}/"
fi

chmod +x "${INSTALL_DIR}/api-consulta"
mkdir -p "${INSTALL_DIR}/data" "${INSTALL_DIR}/logs"

if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  cp "${SCRIPT_DIR}/env.example" "${INSTALL_DIR}/.env"
  echo "Arquivo .env criado em ${INSTALL_DIR}/.env — configure HUB_TOKEN antes de usar."
fi
chmod 600 "${INSTALL_DIR}/.env"

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"

UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
sed \
  -e "s|@INSTALL_DIR@|${INSTALL_DIR}|g" \
  -e "s|@SERVICE_USER@|${SERVICE_USER}|g" \
  -e "s|@SERVICE_PORT@|${SERVICE_PORT}|g" \
  "${SCRIPT_DIR}/api-consulta-cpf.service" > "${UNIT_PATH}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"
systemctl start "${SERVICE_NAME}.service"

echo
echo "Instalacao concluida."
echo "  Pasta:   ${INSTALL_DIR}"
echo "  Servico: ${SERVICE_NAME}"
echo "  URL:     http://<servidor>:${SERVICE_PORT}"
echo
echo "Configure o token:"
echo "  sudo nano ${INSTALL_DIR}/.env"
echo "  sudo systemctl restart ${SERVICE_NAME}"
echo
systemctl --no-pager status "${SERVICE_NAME}"
