#!/usr/bin/env bash
# Factory burn-in — health and services only (before customer setup).
set -euo pipefail

INSTALL_ROOT="${FROGSWORK_INSTALL_ROOT:-/opt/frogswork}"
BASE="${FROGSWORK_BASE:-http://localhost}"

echo "==> Factory burn-in starting"

curl -sf "$BASE/api/health" | python3 -m json.tool

for svc in frogswork-api nginx avahi-daemon smbd; do
  systemctl is-active --quiet "$svc"
  echo "  $svc: active"
done

mountpoint -q /data
df -h /data | tail -1

sudo testparm -s >/dev/null
echo "  samba config: OK"

if [[ -f "${INSTALL_ROOT}/helper/FrogsWork.Helper.exe" ]]; then
  test -s "${INSTALL_ROOT}/helper/FrogsWork.Helper.exe"
  echo "  helper exe: present"
elif [[ -f /var/lib/frogswork/helper/FrogsWork.Helper.exe ]]; then
  test -s /var/lib/frogswork/helper/FrogsWork.Helper.exe
  echo "  helper exe: installed"
else
  echo "ERROR: Helper executable missing" >&2
  exit 1
fi

STATUS="$(curl -sf "$BASE/api/setup/status")"
if echo "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert not d['setup_complete'], d"; then
  echo "  setup: awaiting customer claim"
else
  echo "WARN: setup already complete (dev unit?)" >&2
fi

echo "==> Factory burn-in passed"
