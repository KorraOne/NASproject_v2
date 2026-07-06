#!/usr/bin/env bash
# P0 automated checks on the appliance (manual items listed at end).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="${FROGSWORK_BASE:-http://localhost}"

echo "=============================================="
echo " FrogsWork P0 checklist (automated portion)"
echo "=============================================="

bash "${SCRIPT_DIR}/smoke-m9.sh"

echo ""
echo "==> Production posture"
if [[ -f /etc/sudoers.d/korra ]]; then
  echo "WARN: passwordless sudo drop-in for korra still present (A8)" >&2
else
  echo "  no korra sudoers drop-in: OK"
fi

OWNER="$(stat -c '%U' /opt/frogswork 2>/dev/null || echo unknown)"
echo "  /opt/frogswork owner: ${OWNER}"
if [[ "$OWNER" != "root" ]]; then
  echo "WARN: production install should use root ownership (A9)" >&2
fi

echo ""
echo "==> Manual checks still required"
cat <<'EOF'
  A12  Fresh setup wizard on clean unit (or factory-claimed unit)
  A18  Backup restore via dashboard UI
  A20–A24  Windows helper: download, connect, W: drive, read/write
  A27  Reboot NUC and verify services without SSH
  A28  Confirm nightly snapshot timer (or wait for 02:00 run)
  A30–A32  Customer quick-start and support docs handed over
EOF

echo ""
echo "Full checklist: docs/commercial-ship-checklist.md"
