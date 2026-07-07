#!/usr/bin/env bash
# Apply a previously-downloaded FrogsWork release tarball in-place.
#
# The API downloads a verified tarball to:
#   /var/lib/frogswork/updates/pending.tar.gz
#   /var/lib/frogswork/updates/pending.sha256
#
# This script is executed via passwordless sudo by the API user (frogswork),
# but runs as root and performs the atomic swap + service restart.
set -euo pipefail

INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
STATE_DIR="/var/lib/frogswork"
UPDATE_DIR="${STATE_DIR}/updates"
PENDING_TARBALL="${UPDATE_DIR}/pending.tar.gz"
PENDING_SHA="${UPDATE_DIR}/pending.sha256"

if [[ ! -f "${PENDING_TARBALL}" ]]; then
  echo "ERROR: pending update tarball not found at ${PENDING_TARBALL}" >&2
  exit 1
fi
if [[ ! -f "${PENDING_SHA}" ]]; then
  echo "ERROR: pending update sha256 not found at ${PENDING_SHA}" >&2
  exit 1
fi

echo "==> Verifying update SHA256..."
cd "${UPDATE_DIR}"
sha256sum -c "${PENDING_SHA}"

STAGING_PARENT="${INSTALL_ROOT}.update"
STAGING="${STAGING_PARENT}/new"
PREV="${INSTALL_ROOT}.prev"

rm -rf "${STAGING_PARENT}"
mkdir -p "${STAGING}"

echo "==> Stopping API..."
systemctl stop frogswork-api.service || true

echo "==> Extracting update payload..."
tar -xzf "${PENDING_TARBALL}" -C "${STAGING}" --strip-components=1

if [[ ! -f "${STAGING}/backend/pyproject.toml" ]]; then
  echo "ERROR: extracted update missing backend/pyproject.toml" >&2
  exit 1
fi
if [[ ! -d "${STAGING}/dashboard/dist" ]]; then
  echo "ERROR: extracted update missing dashboard/dist (release artifact should include prebuilt dashboard)" >&2
  exit 1
fi

rollback() {
  echo "==> Rolling back..."
  if [[ -d "${PREV}" ]]; then
    rm -rf "${INSTALL_ROOT}" 2>/dev/null || true
    mv "${PREV}" "${INSTALL_ROOT}"
  fi
  systemctl start frogswork-api.service || true
}

echo "==> Swapping install root atomically..."
rm -rf "${PREV}" 2>/dev/null || true
if [[ -d "${INSTALL_ROOT}" ]]; then
  mv "${INSTALL_ROOT}" "${PREV}"
fi
mv "${STAGING}" "${INSTALL_ROOT}"

echo "==> Running deploy scripts (no Node build)..."
export FROGSWORK_PRODUCTION=1
export FROGSWORK_INSTALL_ROOT="${INSTALL_ROOT}"
export FROGSWORK_SKIP_DASHBOARD_BUILD=1
bash "${INSTALL_ROOT}/scripts/install/02-deploy-app.sh" || { rollback; exit 1; }
bash "${INSTALL_ROOT}/scripts/install/03-enable-services.sh" || { rollback; exit 1; }

echo "==> Health check..."
if command -v curl >/dev/null; then
  curl -sf http://localhost/api/health >/dev/null || { rollback; exit 1; }
fi

echo "==> Marking update as applied..."
rm -f "${PENDING_TARBALL}" "${PENDING_SHA}" 2>/dev/null || true

echo "==> Update applied successfully."

