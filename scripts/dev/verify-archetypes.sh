#!/usr/bin/env bash
echo "==> index.html"
cat /opt/frogswork/dashboard/dist/index.html
echo "==> served index"
curl -sf http://localhost/ | head -8
echo "==> archetypes in DB"
/opt/frogswork/venv/bin/python3 <<'PY'
import sqlite3
c = sqlite3.connect("/var/lib/frogswork/frogswork.db")
c.row_factory = sqlite3.Row
for row in c.execute("SELECT id, name, is_system, can_view_all_personal FROM archetypes"):
    print(dict(row))
PY
echo "==> archetypes API (expect 401 without token)"
curl -s -w "\nHTTP:%{http_code}\n" http://localhost/api/archetypes
