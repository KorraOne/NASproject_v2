#!/usr/bin/env bash
# Factory install wrapper — run on a fresh Ubuntu NUC after release tarball is extracted to /opt/frogswork.
# Usage: sudo bash factory-install.sh --serial FW-2026-00042 --claim-code FW-7K3M-9P2Q
set -euo pipefail

INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
SERIAL=""
CLAIM_CODE=""
DEPLOY_USER="${SUDO_USER:-korra}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial) SERIAL="$2"; shift 2 ;;
    --claim-code) CLAIM_CODE="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$SERIAL" || -z "$CLAIM_CODE" ]]; then
  echo "Usage: sudo $0 --serial FW-2026-00042 --claim-code FW-7K3M-9P2Q" >&2
  exit 1
fi

echo "==> FrogsWork factory install"
echo "    Serial: $SERIAL"
echo "    Install root: $INSTALL_ROOT"

export FROGSWORK_PRODUCTION=1
export FROGSWORK_INSTALL_ROOT="$INSTALL_ROOT"
bash "${INSTALL_ROOT}/scripts/install/install.sh"

HELPER_SRC="${INSTALL_ROOT}/helper/FrogsWork.Helper.exe"
HELPER_DST="/var/lib/frogswork/helper/FrogsWork.Helper.exe"
if [[ -f "$HELPER_SRC" ]]; then
  mkdir -p /var/lib/frogswork/helper
  cp "$HELPER_SRC" "$HELPER_DST"
  chown frogswork:frogswork "$HELPER_DST"
  echo "==> Helper installed to $HELPER_DST"
else
  echo "ERROR: Helper exe not found at $HELPER_SRC" >&2
  exit 1
fi

FACTORY_DIR="/var/lib/frogswork/factory"
mkdir -p "$FACTORY_DIR"
echo "$SERIAL" >"${FACTORY_DIR}/serial"
chmod 600 "${FACTORY_DIR}/serial"

"${INSTALL_ROOT}/venv/bin/python3" "${INSTALL_ROOT}/scripts/factory/seed-device-identity.py" \
  --serial "$SERIAL" \
  --claim-code "$CLAIM_CODE"

bash "${INSTALL_ROOT}/scripts/factory/register-unit.sh" \
  --serial "$SERIAL" \
  --claim-code "$CLAIM_CODE" \
  --version "$(cat "${INSTALL_ROOT}/VERSION")"

echo "==> SSH hardening (remote off until owner enables support)"
"${INSTALL_ROOT}/venv/bin/python3" - <<'PY'
from frogswork_api.services.system import init_ssh_for_new_setup
init_ssh_for_new_setup()
PY

if id "${DEPLOY_USER}" &>/dev/null; then
  rm -f "/etc/sudoers.d/${DEPLOY_USER}" 2>/dev/null || true
  echo "==> Removed passwordless sudo for ${DEPLOY_USER}"
fi

systemctl enable frogswork-usb-provision.path frogswork-usb-provision.service 2>/dev/null || true

bash "${INSTALL_ROOT}/scripts/factory/burn-in.sh"

echo "==> Factory install complete"
echo "    Print labels: serial=$SERIAL claim code on inner card"
echo "    See docs/retail-kit-and-labels.md"
