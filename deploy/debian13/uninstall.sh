#!/usr/bin/env bash
# Remove o servico systemd e, opcionalmente, os arquivos em /srv.
set -euo pipefail

INSTALL_DIR="/srv/api-consulta-cpf"
SERVICE_NAME="api-consulta-cpf"
SERVICE_USER="api-consulta"
KEEP_DATA=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-data)
      KEEP_DATA=1
      shift
      ;;
    *)
      echo "Opcao desconhecida: $1"
      echo "Uso: sudo $0 [--keep-data]"
      exit 1
      ;;
  esac
done

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "[ERRO] Execute como root (sudo)."
  exit 1
fi

if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
  systemctl disable --now "${SERVICE_NAME}" || true
fi

UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
if [[ -f "${UNIT_PATH}" ]]; then
  rm -f "${UNIT_PATH}"
  systemctl daemon-reload
fi

if [[ "${KEEP_DATA}" -eq 0 && -d "${INSTALL_DIR}" ]]; then
  rm -rf "${INSTALL_DIR}"
  echo "Removido: ${INSTALL_DIR}"
else
  echo "Dados mantidos em: ${INSTALL_DIR}"
fi

if id "${SERVICE_USER}" &>/dev/null; then
  if [[ "${KEEP_DATA}" -eq 0 ]]; then
    userdel "${SERVICE_USER}" 2>/dev/null || true
  fi
fi

echo "Servico ${SERVICE_NAME} desinstalado."
