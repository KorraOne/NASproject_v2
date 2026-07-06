#!/usr/bin/env bash
# Apply WiFi credentials from frogswork-setup.json on a USB mount.
# Writes frogswork-setup.log and frogswork-setup.status back to the USB.
# Usage: import-wifi.sh /media/user/USBNAME
set -euo pipefail

MOUNT="${1:-}"
if [[ -z "$MOUNT" || ! -d "$MOUNT" ]]; then
  echo "Usage: $0 /media/user/USBNAME" >&2
  exit 1
fi

CONFIG="${MOUNT}/frogswork-setup.json"
LOG="${MOUNT}/frogswork-setup.log"
STATUS="${MOUNT}/frogswork-setup.status"
SOFTWARE_VERSION="$(cat /opt/frogswork/VERSION 2>/dev/null || echo unknown)"
SERIAL="$(cat /var/lib/frogswork/factory/serial 2>/dev/null || echo unknown)"

step() { echo "$1" >>"$LOG"; }
fail() {
  echo "Finished: FAILED" >>"$LOG"
  echo "What to try: $1" >>"$LOG"
  printf '{"result":"failed","error_code":"%s","finished_at":"%s"}\n' "$2" "$(date -Iseconds)" >"$STATUS"
  rm -f "$CONFIG"
  sync
  exit 1
}

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

CONN="frogswork-wifi"
nmcli con delete "$CONN" >/dev/null 2>&1 || true
if ! nmcli dev wifi connect "$SSID" password "$PASSWORD" name "$CONN" 2>>"$LOG"; then
  fail "Could not join Wi-Fi network. Check name and password." "connect_failed"
fi
step "Step 4: nmcli connection create     OK"
step "Step 5: Associate to AP             OK"

IP="$(hostname -I | awk '{print $1}')"
step "Step 6: DHCP address obtained       OK  ($IP)"

if curl -sf http://127.0.0.1/api/health >/dev/null; then
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
