"""Reset dashboard admin password on dev NUC (for smoke tests only)."""
import sqlite3
import sys

from frogswork_api.auth.security import hash_password

password = sys.argv[1] if len(sys.argv) > 1 else "FrogsWork-Dev-2026"
db = "/var/lib/frogswork/frogswork.db"
h = hash_password(password)
with sqlite3.connect(db) as conn:
    conn.execute(
        "UPDATE dashboard_admin SET password_hash = ? WHERE id = 1",
        (h,),
    )
print(f"Updated admin password to: {password}")
