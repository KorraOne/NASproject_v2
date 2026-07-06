"""Share root and Personal container ACL sync."""

from __future__ import annotations

import os
import sqlite3

from pathlib import Path

from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.integrations.linux_users import (
    SUPERUSER_GROUP,
    _path_exists,
    apply_private_folder_permissions,
    ensure_personal_container,
)
from frogswork_api.paths import DATA_FROGSWORK, DATA_PERSONAL


def create_shared_folder_directory(path: Path) -> None:
    """Create a team folder at share root (requires root)."""
    if path.exists():
        raise IntegrationError(f"Path already exists: {path}")
    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        path.mkdir(parents=True, exist_ok=False)
        return
    run_cmd("mkdir", "-p", str(path))
    run_cmd("chown", "root:root", str(path))
    run_cmd("chmod", "2770", str(path))


def remove_shared_folder_directory(path: Path) -> None:
    if not path.exists():
        return
    if os.environ.get("FROGSWORK_SKIP_SYSTEM") == "1":
        path.rmdir()
        return
    run_cmd("rmdir", str(path))


def _reset_container_acl(path: str) -> None:
    run_cmd("chown", "root:root", path)
    run_cmd("chmod", "711", path)
    run_cmd("setfacl", "-b", path)


def sync_share_root_acl(usernames: list[str]) -> None:
    """Apply share root and Personal container ACLs.

    Users get read+execute on the share root and Personal container so Samba can
    list entries. ``hide unreadable`` plus per-folder ACLs hide team folders and
    other people's private homes.
    """
    ensure_personal_container()
    root = str(DATA_FROGSWORK)
    personal = str(DATA_PERSONAL)

    _reset_container_acl(root)
    _reset_container_acl(personal)

    for username in usernames:
        run_cmd("setfacl", "-m", f"u:{username}:r-x", root)
        run_cmd("setfacl", "-m", f"u:{username}:r-x", personal)

    run_cmd("setfacl", "-m", f"g:{SUPERUSER_GROUP}:r-x", root)
    run_cmd("setfacl", "-m", f"g:{SUPERUSER_GROUP}:r-x", personal)
    run_cmd("setfacl", "-m", "m:rwx", root)
    run_cmd("setfacl", "-m", "o:---", root)
    run_cmd("setfacl", "-m", "m:rwx", personal)
    run_cmd("setfacl", "-m", "o:---", personal)


def sync_all_layout_acls(conn: sqlite3.Connection) -> None:
    """Re-sync share root, Personal container, and every private home."""
    from frogswork_api.services import elevations as elevation_service

    rows = conn.execute("SELECT id, username FROM file_users ORDER BY username").fetchall()
    usernames = [row["username"] for row in rows]
    sync_share_root_acl(usernames)
    for row in rows:
        home = DATA_PERSONAL / row["username"]
        if _path_exists(home):
            elevation_service.sync_personal_folder_acl(conn, row["id"])
