"""Helper app mount list for file users."""

from __future__ import annotations

from fastapi import HTTPException, status

from frogswork_api.db import connect
from frogswork_api.paths import PERSONAL_CONTAINER_NAME, SAMBA_SHARE_NAME


def get_mounts_for_user(username: str, host: str) -> dict:
    with connect() as conn:
        user = conn.execute(
            "SELECT id, username, display_name FROM file_users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File user not found.",
            )

        personal_share = f"{SAMBA_SHARE_NAME}/{PERSONAL_CONTAINER_NAME}/{user['username']}"
        mounts: list[dict] = [
            {
                "label": "FrogsWork",
                "share": SAMBA_SHARE_NAME,
                "unc_path": _unc(host, SAMBA_SHARE_NAME),
                "suggested_letter": "W",
                "kind": "root",
                "access": "read_write",
                "personal_path": _unc(host, personal_share),
            }
        ]

    return {
        "hostname": host,
        "username": user["username"],
        "display_name": user["display_name"],
        "mounts": mounts,
    }


def _unc(host: str, share: str) -> str:
    return f"\\\\{host}\\{share.replace('/', '\\')}"
