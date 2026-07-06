#!/bin/bash
# M3 smoke test — run on NUC after deploy (requires setup complete + admin password).
set -euo pipefail

ADMIN_PASS="${FROGSWORK_ADMIN_PASS:-FrogsWork-Dev-2026}"
BASE="${FROGSWORK_BASE:-http://localhost}"

TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo "==> Create file user alice"
curl -sf -X POST "$BASE/api/users" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d '{"username":"alice","display_name":"Alice","password":"alice-file-pass"}'
echo

echo "==> Linux + Samba"
id alice
pdbedit -L | grep -i alice || sudo pdbedit -L | grep -i alice
ls -la /data/frogswork/Personal/alice
getfacl /data/frogswork/Personal/alice | head -8
stat -c '%a %U:%G' /data/frogswork/Personal/alice

echo "==> SMB auth test (optional — requires smbclient)"
if command -v smbclient >/dev/null; then
  smbclient -L //localhost -U 'alice%alice-file-pass' -m SMB3 2>/dev/null | head -5
else
  sudo pdbedit -L | grep -i alice
fi

echo "==> M3 smoke OK"
