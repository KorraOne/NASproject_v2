#!/usr/bin/env bash
set -euo pipefail

BASE="${FROGSWORK_BASE:-http://localhost}"
ADMIN_PASS="${FROGSWORK_ADMIN_PASS:-FrogsWork-Dev-2026}"

echo "==> Health"
curl -sf "$BASE/api/health" | python3 -m json.tool

echo "==> Public info"
curl -sf "$BASE/api/public/info" | python3 -m json.tool

TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"password\":\"$ADMIN_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

echo "==> Archetypes"
curl -sf "$BASE/api/archetypes" -H "$AUTH" | python3 -m json.tool

echo "==> Storage overview"
curl -sf "$BASE/api/storage" -H "$AUTH" | python3 -m json.tool | head -15

echo "==> Dashboard static assets"
curl -sf -o /dev/null -w "index.html: %{http_code}\n" "$BASE/"
curl -sf -o /dev/null -w "dashboard JS: %{http_code}\n" "$(curl -sf "$BASE/" | grep -o '/assets/index-[^\"]*\.js' | head -1 | sed "s|^|$BASE|")"

echo "==> Verify deploy OK"
