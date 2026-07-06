#!/usr/bin/env bash
# Run on nuc1 via: ssh nuc1 'bash -s' < scripts/dev/nuc-smoke-remote.sh
set -euo pipefail

ADMIN_PASS="${FROGSWORK_ADMIN_PASS:-FrogsWork-Dev-2026}"
BASE="${FROGSWORK_BASE:-http://localhost}"

echo "==> Login test"
TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "  token: ${TOKEN:0:20}..."

AUTH="Authorization: Bearer $TOKEN"

echo "==> Archetypes"
curl -sf "$BASE/api/archetypes" -H "$AUTH" | python3 -c "import sys,json; names={a['name'] for a in json.load(sys.stdin)}; assert 'Super User' in names; print('  OK:', names)"

echo "==> Effective permissions"
curl -sf "$BASE/api/permissions/effective" -H "$AUTH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  {len(d)} users')"

echo "==> Dashboard"
CODE=$(curl -sf -o /dev/null -w '%{http_code}' "$BASE/")
test "$CODE" = "200"
JS=$(curl -sf "$BASE/" | grep -o 'index-[^"]*\.js' | head -1)
echo "  bundle: $JS"

echo "==> Helper download"
HELPER_OUT=$(curl -sf -o /dev/null -w '%{http_code} %{size_download}' "$BASE/api/helper/download")
echo "  HTTP $HELPER_OUT"
case "$HELPER_OUT" in 200\ *) ;; *) exit 1 ;; esac

echo "==> Snapshots"
curl -sf "$BASE/api/snapshots" -H "$AUTH" | python3 -c "import sys,json; print(f'  {len(json.load(sys.stdin))} snapshots')"
curl -sf -X POST "$BASE/api/snapshots" -H "$AUTH" >/dev/null 2>&1 || true

echo "==> Full smoke-m9"
bash /opt/frogswork/scripts/dev/smoke-m9.sh

echo "==> NUC validation OK"
