#!/usr/bin/env bash
# Move private homes from flat /data/frogswork/{user} to /data/frogswork/Personal/{user}.
set -euo pipefail

ROOT="/data/frogswork"
PERSONAL="${ROOT}/Personal"
DB="/var/lib/frogswork/frogswork.db"

echo "==> Creating Personal container ${PERSONAL}"
mkdir -p "${PERSONAL}"

echo "==> Discovering team folder names from database"
TEAM_NAMES=""
if [[ -f "${DB}" ]]; then
  TEAM_NAMES=$(python3 <<'PY'
import sqlite3
from pathlib import Path
db = Path("/var/lib/frogswork/frogswork.db")
if not db.exists():
    raise SystemExit(0)
conn = sqlite3.connect(db)
for (name,) in conn.execute("SELECT name FROM shared_folders"):
    print(name)
PY
)
fi

echo "==> Moving user homes into Personal/"
shopt -s nullglob
for path in "${ROOT}"/*; do
  [[ -d "$path" ]] || continue
  name="$(basename "$path")"
  [[ "$name" == "Personal" ]] && continue
  if echo "${TEAM_NAMES}" | grep -qxF "$name"; then
    continue
  fi
  if [[ ! -e "${PERSONAL}/${name}" ]]; then
    echo "  ${name} -> Personal/${name}"
    mv "$path" "${PERSONAL}/${name}"
  fi
done

echo "==> Updating Linux home directories"
if [[ -f "${DB}" ]]; then
  while IFS= read -r user; do
    [[ -n "$user" ]] || continue
    if id "$user" &>/dev/null; then
      usermod --home "${PERSONAL}/${user}" "$user" 2>/dev/null || true
    fi
  done < <(python3 <<'PY'
import sqlite3
conn = sqlite3.connect("/var/lib/frogswork/frogswork.db")
for (username,) in conn.execute("SELECT username FROM file_users ORDER BY username"):
    print(username)
PY
)
fi

echo "==> Installing updated Samba config"
install -m 644 /opt/frogswork/scripts/samba/templates/smb.conf /etc/samba/smb.conf

echo "==> Re-syncing ACL layout via API module"
python3 <<'PY'
import sqlite3
import sys
sys.path.insert(0, "/opt/frogswork/backend")
from frogswork_api.db import connect
from frogswork_api.integrations.share_layout import sync_all_layout_acls

with connect() as conn:
    sync_all_layout_acls(conn)
print("ACL layout synced.")
PY

echo "==> Ensuring file users are in frogswork-users group"
groupadd -f frogswork-users
if [[ -f "${DB}" ]]; then
  while IFS= read -r user; do
    [[ -n "$user" ]] || continue
    if id "$user" &>/dev/null; then
      getent group frogswork-users | grep -q "\b${user}\b" || usermod -aG frogswork-users "$user" 2>/dev/null || true
    fi
  done < <(python3 <<'PY'
import sqlite3
conn = sqlite3.connect("/var/lib/frogswork/frogswork.db")
for (username,) in conn.execute("SELECT username FROM file_users ORDER BY username"):
    print(username)
PY
)
fi

echo "==> Reloading Samba"
testparm -s >/dev/null
systemctl reload smbd

echo "==> Personal folder migration complete."
echo "    Windows users should refresh W: in Explorer (F5) or use helper Refresh folders."
