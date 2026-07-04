#!/usr/bin/env bash
# Create a readonly btrfs snapshot of /data.
set -euo pipefail

INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
VENV="${INSTALL_ROOT}/venv/bin/python"

if [[ ! -x "${VENV}" ]]; then
  echo "ERROR: Python venv not found at ${VENV}" >&2
  exit 1
fi

exec "${VENV}" - <<'PY'
from frogswork_api.integrations import btrfs
from frogswork_api.integrations._run import IntegrationError

try:
    info = btrfs.create_daily_snapshot()
    print(f"Created snapshot {info.id}")
except IntegrationError as exc:
    message = str(exc)
    if "already exists" in message:
        print(message)
        raise SystemExit(0)
    print(f"ERROR: {message}", flush=True)
    raise SystemExit(1)
PY
