#!/bin/bash
# M4 smoke test — folder permissions, ACL, and Samba share sync on NUC.
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
PROJECTS_ID=$(curl -sf "$BASE/api/folders" -H "$AUTH" | python3 -c "import sys,json; print(next(f['id'] for f in json.load(sys.stdin) if f['name']=='Projects'))")

echo "==> Assign Projects: alice read, bob read_write"
curl -sf -X PUT "$BASE/api/folders/$PROJECTS_ID/permissions" \
  -H "Content-Type: application/json" -H "$AUTH" \
  -d "{\"permissions\":[{\"user_id\":$ALICE_ID,\"access\":\"read\"},{\"user_id\":$BOB_ID,\"access\":\"read_write\"}]}"
echo

echo "==> Samba share fragment"
sudo cat /etc/samba/shares.d/Projects.conf

echo "==> ACL on /data/shared/Projects"
getfacl /data/shared/Projects | head -20

echo "==> testparm"
sudo testparm -s >/dev/null

echo "==> M4 smoke OK"
