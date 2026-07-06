#!/usr/bin/env bash
# Migrate legacy /data/users + /data/shared layout to unified /data/frogswork share.
set -euo pipefail

ROOT="/data/frogswork"
USERS_OLD="/data/users"
SHARED_OLD="/data/shared"

echo "==> Creating unified share root ${ROOT}"
mkdir -p "${ROOT}"

if [[ -d "${USERS_OLD}" ]]; then
  echo "==> Moving user homes from ${USERS_OLD}"
  for path in "${USERS_OLD}"/*; do
    [[ -e "$path" ]] || continue
    name="$(basename "$path")"
    if [[ ! -e "${ROOT}/${name}" ]]; then
      mv "$path" "${ROOT}/${name}"
    fi
  done
  rmdir "${USERS_OLD}" 2>/dev/null || true
fi

if [[ -d "${SHARED_OLD}" ]]; then
  echo "==> Moving shared folders from ${SHARED_OLD}"
  for path in "${SHARED_OLD}"/*; do
    [[ -e "$path" ]] || continue
    name="$(basename "$path")"
    if [[ ! -e "${ROOT}/${name}" ]]; then
      mv "$path" "${ROOT}/${name}"
    fi
  done
  rmdir "${SHARED_OLD}" 2>/dev/null || true
fi

echo "==> Installing unified Samba config"
install -m 644 /opt/frogswork/scripts/samba/templates/smb.conf /etc/samba/smb.conf

echo "==> Removing legacy per-folder share fragments"
rm -f /etc/samba/shares.d/*.conf
echo "# legacy fragments removed — unified [frogswork] share" > /etc/samba/shares.d/00-placeholder.conf

echo "==> Ensuring frogswork-users group exists"
groupadd -f frogswork-users
for user in $(getent passwd | awk -F: '$6 ~ /^\/data\/frogswork\// {print $1}'); do
  getent group frogswork-users | grep -q "\b${user}\b" || usermod -aG frogswork-users "$user" 2>/dev/null || true
done

echo "==> Updating folder paths in database"
python3 <<'PY'
import sqlite3
from pathlib import Path

db = Path("/var/lib/frogswork/frogswork.db")
if not db.exists():
    print("No database — skip path update")
    raise SystemExit(0)

conn = sqlite3.connect(db)
rows = conn.execute("SELECT id, name, path FROM shared_folders").fetchall()
for row_id, name, old_path in rows:
    new_path = f"/data/frogswork/{name}"
    if old_path != new_path:
        conn.execute("UPDATE shared_folders SET path = ? WHERE id = ?", (new_path, row_id))
conn.commit()
print(f"Updated {len(rows)} shared folder path(s)")
PY

echo "==> Reloading Samba"
testparm -s >/dev/null
systemctl reload smbd

echo "==> Migration complete. Run sync ACL from dashboard or: frogswork-api sync (if available)"
echo "    Users should disconnect old U:/S: drives and reconnect helper for W: drive."
