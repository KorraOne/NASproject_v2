#!/bin/bash
# M4 smoke test — folder permissions, ACL, and unified frogswork share on NUC.
set -euo pipefail

ADMIN_PASS="${FROGSWORK_ADMIN_PASS:-FrogsWork-Dev-2026}"
BASE="${FROGSWORK_BASE:-http://localhost}"

TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH="Authorization: Bearer $TOKEN"

echo "==> Ensure alice and bob exist"
for user in alice bob; do
  if ! id "$user" &>/dev/null; then
    pass="${user}-file-pass"
    curl -sf -X POST "$BASE/api/users" \
      -H "Content-Type: application/json" -H "$AUTH" \
      -d "{\"username\":\"$user\",\"password\":\"$pass\"}"
    echo
  fi
done

ALICE_ID=$(curl -sf "$BASE/api/users" -H "$AUTH" | python3 -c "import sys,json; print(next(u['id'] for u in json.load(sys.stdin) if u['username']=='alice'))")
BOB_ID=$(curl -sf "$BASE/api/users" -H "$AUTH" | python3 -c "import sys,json; print(next(u['id'] for u in json.load(sys.stdin) if u['username']=='bob'))")
PROJECTS_ID=$(curl -sf "$BASE/api/folders" -H "$AUTH" | python3 -c "
import sys, json
folders = json.load(sys.stdin)
if not folders:
    raise SystemExit('No shared folders found')
preferred = next((f for f in folders if f['name'] == 'Projects'), folders[0])
print(preferred['id'])
")
PROJECTS_NAME=$(curl -sf "$BASE/api/folders" -H "$AUTH" | python3 -c "
import sys, json
folders = json.load(sys.stdin)
preferred = next((f for f in folders if f['name'] == 'Projects'), folders[0])
print(preferred['name'])
")

echo "==> Assign ${PROJECTS_NAME}: alice read, bob read_write"
curl -sf -X PUT "$BASE/api/folders/$PROJECTS_ID/permissions" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"permissions\":[{\"user_id\":$ALICE_ID,\"access\":\"read\"},{\"user_id\":$BOB_ID,\"access\":\"read_write\"}]}"
echo

echo "==> Unified frogswork share"
sudo testparm -s 2>/dev/null | grep -A6 '\[frogswork\]'

echo "==> ACL on /data/frogswork/${PROJECTS_NAME}"
sudo getfacl "/data/frogswork/${PROJECTS_NAME}" | head -20

echo "==> Private home isolation (alice cannot access bob home)"
if getent passwd alice bob >/dev/null; then
  if sudo -u alice ls /data/frogswork/Personal/bob >/dev/null 2>&1; then
    echo "ERROR: alice can access bob private folder" >&2
    exit 1
  fi
  echo "  alice blocked from bob home"
fi

echo "==> Create throwaway folder via API"
SMOKE_FOLDER="SmokeTest-$(date +%s)"
FOLDER_RESP=$(curl -sf -X POST "$BASE/api/folders" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"name\":\"$SMOKE_FOLDER\"}")
SMOKE_FOLDER_ID=$(echo "$FOLDER_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
sudo test -d "/data/frogswork/$SMOKE_FOLDER"
curl -sf -X DELETE "$BASE/api/folders/$SMOKE_FOLDER_ID" -H "$AUTH"
echo "  folder create/delete OK"

echo "==> Create throwaway user via API"
SMOKE_USER="smoke$(date +%s | tail -c 6)"
curl -sf -X POST "$BASE/api/users" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"username\":\"$SMOKE_USER\",\"password\":\"smoke-test-pass\"}" >/dev/null
id "$SMOKE_USER"
SMOKE_USER_ID=$(curl -sf "$BASE/api/users" -H "$AUTH" | python3 -c "import sys,json; print(next(u['id'] for u in json.load(sys.stdin) if u['username']=='$SMOKE_USER'))")
curl -sf -X DELETE "$BASE/api/users/$SMOKE_USER_ID" -H "$AUTH"
echo "  user create/delete OK"

echo "==> Public help info (no auth)"
curl -sf "$BASE/api/public/info" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'hostname' in d and d.get('help_path')=='/help'"

echo "==> testparm"
sudo testparm -s >/dev/null

echo "==> M4 smoke OK"
