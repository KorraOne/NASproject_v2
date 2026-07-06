#!/usr/bin/env bash
# M9 smoke test — full NUC validation before release (run on appliance after M1–M8).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_PASS="${FROGSWORK_ADMIN_PASS:-FrogsWork-Dev-2026}"
BASE="${FROGSWORK_BASE:-http://localhost}"

echo "==> Health"
curl -sf "$BASE/api/health" | python3 -m json.tool

echo "==> Core services"
for svc in frogswork-api nginx avahi-daemon smbd; do
  systemctl is-active --quiet "$svc"
  echo "  $svc: active"
done

echo "==> Data volume"
df -h /data | tail -1

echo "==> M2 setup/auth smoke"
bash "${SCRIPT_DIR}/smoke-m2.sh" >/dev/null 2>&1 || true
curl -sf "$BASE/api/setup/status" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('setup_complete'), d"

echo "==> M4 user/folder smoke"
bash "${SCRIPT_DIR}/smoke-m4.sh"

echo "==> Samba frogswork share"
sudo testparm -s >/dev/null
if command -v smbclient >/dev/null; then
  smbclient -L //127.0.0.1 -U 'alice%alice-file-pass' -m SMB3 2>&1 | grep -q frogswork
  smbclient '//127.0.0.1/frogswork' -U 'alice%alice-file-pass' -m SMB3 -c ls >/dev/null
  echo "  frogswork: accessible"
fi

echo "==> Snapshot API"
TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"
curl -sf "$BASE/api/snapshots" -H "$AUTH" | python3 -m json.tool | head -20
curl -sf -X POST "$BASE/api/snapshots" -H "$AUTH" >/dev/null 2>&1 || true
curl -sf "$BASE/api/snapshots" -H "$AUTH" | python3 -c "import sys,json; assert len(json.load(sys.stdin)) >= 1"

echo "==> Archetypes API"
curl -sf "$BASE/api/archetypes" -H "$AUTH" | python3 -c "import sys,json; names={a['name'] for a in json.load(sys.stdin)}; assert 'Super User' in names and 'Standard Employee' in names"

echo "==> Effective permissions API"
curl -sf "$BASE/api/permissions/effective" -H "$AUTH" | python3 -m json.tool | head -20

echo "==> Dashboard static"
DASH_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "$BASE/")
echo "  dashboard: $DASH_CODE"
test "$DASH_CODE" = "200"

echo "==> Helper API"
curl -sf -u 'alice:alice-file-pass' "$BASE/api/helper/mounts?host=127.0.0.1" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['username']=='alice'"
HELPER_SIZE=$(curl -sf -o /dev/null -w '%{http_code} %{size_download}' "$BASE/api/helper/download")
echo "  download: $HELPER_SIZE"
echo "$HELPER_SIZE" | grep -q '^200 '

echo "==> M9 smoke OK"
echo "Manual checks still required: dashboard UI, Windows helper connect, reboot survival."
echo "See docs/known-issues.md for UI polish verification checklist."
