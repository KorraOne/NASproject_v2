#!/usr/bin/env bash
# Delete expired snapshots per retention policy in SQLite settings.
set -euo pipefail

INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
VENV="${INSTALL_ROOT}/venv/bin/python"

if [[ ! -x "${VENV}" ]]; then
  echo "ERROR: Python venv not found at ${VENV}" >&2
  exit 1
fi

exec "${VENV}" - <<'PY'
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.services.retention import apply_retention

try:
    apply_retention()
    print("Retention policy applied.")
except IntegrationError as exc:
    print(f"ERROR: {exc}", flush=True)
    raise SystemExit(1)
PY
