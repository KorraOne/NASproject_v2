"""Helper app mount list for file users."""

from __future__ import annotations

import sqlite3

from fastapi import HTTPException, status

from frogswork_api.db import connect
from frogswork_api.integrations.samba_shares import share_name

SHARED_DRIVE_LETTERS = "STVWXYZ"


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

        mounts: list[dict] = [
            {
                "label": "My files",
                "share": user["username"],
                "unc_path": _unc(host, user["username"]),
                "suggested_letter": "U",
                "kind": "private",
                "access": "read_write",
            }
        ]

        rows = conn.execute(
            """
            SELECT sf.name, fp.access
            FROM folder_permissions fp
            JOIN shared_folders sf ON sf.id = fp.shared_folder_id
            WHERE fp.file_user_id = ?
            ORDER BY sf.name COLLATE NOCASE
            """,
            (user["id"],),
        ).fetchall()
        mounts.extend(_shared_mounts(host, rows))

    return {
        "hostname": host,
        "username": user["username"],
        "display_name": user["display_name"],
        "mounts": mounts,
    }


def _unc(host: str, share: str) -> str:
    return f"\\\\{host}\\{share}"


def _shared_mounts(host: str, rows: list[sqlite3.Row]) -> list[dict]:
    mounts: list[dict] = []
    letters = iter(SHARED_DRIVE_LETTERS)
    for row in rows:
        share = share_name(row["name"])
        letter = next(letters, None)
        if letter is None:
            break
        mounts.append(
            {
                "label": row["name"],
                "share": share,
                "unc_path": _unc(host, share),
                "suggested_letter": letter,
                "kind": "shared",
                "access": row["access"],
            }
        )
    return mounts
