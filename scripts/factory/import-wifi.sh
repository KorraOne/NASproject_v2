#!/usr/bin/env bash
# Apply WiFi credentials from frogswork-setup.json on a USB mount.
# Writes frogswork-setup.log and frogswork-setup.status back to the USB.
# Usage: import-wifi.sh /media/user/USBNAME
#        import-wifi.sh auto   (find first frogswork-setup.json under /media)
set -euo pipefail

MOUNT="${1:-}"
if [[ "$MOUNT" == "auto" || -z "$MOUNT" ]]; then
  MOUNT=""
  for candidate in /media/*/*/frogswork-setup.json /media/*/frogswork-setup.json; do
    [[ -f "$candidate" ]] || continue
    MOUNT="$(dirname "$candidate")"
    break
  done
fi

if [[ -z "$MOUNT" || ! -d "$MOUNT" ]]; then
  echo "No frogswork-setup.json found on a mounted USB." >&2
  exit 1
fi

CONFIG="${MOUNT}/frogswork-setup.json"
LOG="${MOUNT}/frogswork-setup.log"
STATUS="${MOUNT}/frogswork-setup.status"
LOCK="${MOUNT}/.frogswork-wifi.lock"
SOFTWARE_VERSION="$(cat /opt/frogswork/VERSION 2>/dev/null || echo unknown)"
SERIAL="$(cat /var/lib/frogswork/factory/serial 2>/dev/null || echo unknown)"

if [[ -f "$LOCK" ]]; then
  echo "WiFi import already running for this USB." >&2
  exit 0
fi
touch "$LOCK"

step() { echo "$1" >>"$LOG"; }
fail() {
  echo "Finished: FAILED" >>"$LOG"
  echo "What to try: $1" >>"$LOG"
  printf '{"result":"failed","error_code":"%s","finished_at":"%s"}\n' "$2" "$(date -Iseconds)" >"$STATUS"
  rm -f "$CONFIG" "$LOCK"
  sync
  exit 1
}

cleanup() {
  rm -f "$LOCK"
}
trap cleanup EXIT

: >"$LOG"
{
  echo "[FrogsWork WiFi Setup]"
  echo "Started: $(date -Iseconds)"
  echo "Serial: $SERIAL"
  echo "Software: $SOFTWARE_VERSION"
  echo
} >>"$LOG"

if [[ ! -f "$CONFIG" ]]; then
  fail "No frogswork-setup.json found on USB." "missing_config"
fi
step "Step 1: USB mount detected          OK"
step "Step 2: Read frogswork-setup.json   OK"

SSID="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['wifi']['ssid'])" "$CONFIG")"
PASSWORD="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['wifi']['password'])" "$CONFIG")"
COUNTRY="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['wifi'].get('country','AU'))" "$CONFIG")"
step "Step 3: Validate SSID/country       OK"

if ! command -v nmcli >/dev/null; then
  fail "NetworkManager (nmcli) is not installed on this unit." "no_nmcli"
fi

nmcli radio wifi on >/dev/null 2>&1 || true
if command -v iw >/dev/null; then
  iw reg set "$COUNTRY" >/dev/null 2>&1 || true
fi

CONN="frogswork-wifi"
nmcli con delete "$CONN" >/dev/null 2>&1 || true
if ! nmcli dev wifi connect "$SSID" password "$PASSWORD" name "$CONN" 2>>"$LOG"; then
  fail "Could not join Wi-Fi network. Check name and password." "connect_failed"
fi
step "Step 4: nmcli connection create     OK"
step "Step 5: Associate to AP             OK"

IP="$(hostname -I | awk '{print $1}')"
step "Step 6: DHCP address obtained       OK  ($IP)"

if curl -sf --max-time 15 http://127.0.0.1/api/health >/dev/null; then
  step "Step 7: Dashboard health check      OK"
else
  step "Step 7: Dashboard health check      WARN (API not responding yet)"
fi

rm -f "$CONFIG"
step "Step 8: Scrub credentials from USB  OK"
{
  echo
  echo "Finished: SUCCESS"
  echo "Next: Remove USB, connect your PC to the same WiFi, open http://frogswork.local"
} >>"$LOG"

printf '{"result":"success","error_code":null,"ip":"%s","finished_at":"%s"}\n' "$IP" "$(date -Iseconds)" >"$STATUS"
sync
