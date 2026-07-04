"""POSIX ACL sync for shared folders."""

from __future__ import annotations

from pathlib import Path

from frogswork_api.integrations._run import run_cmd

AccessLevel = str  # "read" | "read_write"


def sync_shared_folder_acl(folder_path: Path, permissions: list[tuple[str, AccessLevel]]) -> None:
    """Apply user ACLs on a shared folder. Clears prior ACL entries first."""
    path = str(folder_path)
    run_cmd("chown", "root:root", path)
    run_cmd("chmod", "2770", path)
    run_cmd("setfacl", "-b", path)

    for username, access in permissions:
        mode = "rwx" if access == "read_write" else "r-x"
        run_cmd("setfacl", "-m", f"u:{username}:{mode}", path)
        run_cmd("setfacl", "-d", "-m", f"u:{username}:{mode}", path)

    run_cmd("setfacl", "-m", "m:rwx", path)
    run_cmd("setfacl", "-m", "o:---", path)
