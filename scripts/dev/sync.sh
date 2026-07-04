#!/usr/bin/env bash
# Sync repo to the NUC and re-run deploy (Windows-friendly: tar over SSH if rsync missing).
set -euo pipefail

HOST="${FROGSWORK_HOST:-nuc1}"
INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

TAR_EXCLUDES=(
  --exclude=.git
  --exclude=.cursor
  --exclude=node_modules
  --exclude=dashboard/dist
  --exclude=backend/.venv
  --exclude=helper/FrogsWork.Helper/bin
  --exclude=helper/FrogsWork.Helper/obj
  --exclude='**/__pycache__'
)

sync_rsync() {
  local -a rsync_ex=(
    --exclude .git --exclude .cursor --exclude node_modules
    --exclude dashboard/dist --exclude backend/.venv
    --exclude helper/**/bin --exclude helper/**/obj
    --exclude "**/__pycache__"
  )
  ssh "${HOST}" "sudo mkdir -p ${INSTALL_ROOT} && sudo chown -R \$(whoami):\$(whoami) ${INSTALL_ROOT}"
  rsync -avz --delete "${rsync_ex[@]}" -e ssh "${REPO_ROOT}/" "${HOST}:${INSTALL_ROOT}/"
}

sync_tar() {
  ssh "${HOST}" "sudo mkdir -p ${INSTALL_ROOT} && sudo chown -R \$(whoami):\$(whoami) ${INSTALL_ROOT}"
  tar -cf - "${TAR_EXCLUDES[@]}" -C "${REPO_ROOT}" . | ssh "${HOST}" "tar -xf - -C ${INSTALL_ROOT}"
}

echo "==> Syncing to ${HOST}:${INSTALL_ROOT}/"
if command -v rsync >/dev/null 2>&1; then
  sync_rsync
else
  echo "    (rsync not found — using tar over SSH)"
  sync_tar
fi

echo "==> Normalising shell script line endings..."
ssh "${HOST}" "find ${INSTALL_ROOT}/scripts -name '*.sh' -exec sed -i 's/\\r$//' {} +"

echo "==> Running deploy on ${HOST}..."
ssh "${HOST}" "sudo bash ${INSTALL_ROOT}/scripts/install/02-deploy-app.sh && sudo bash ${INSTALL_ROOT}/scripts/install/03-enable-services.sh"

echo "==> Health check..."
ssh "${HOST}" "curl -sf http://localhost/api/health" && echo

echo "==> Sync complete."
