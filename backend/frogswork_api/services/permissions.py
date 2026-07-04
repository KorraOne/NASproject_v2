"""Shared folder permission matrix — single source of truth."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, status

from frogswork_api.db import connect
from frogswork_api.integrations import acl, samba_shares
from frogswork_api.integrations._run import IntegrationError

Access = Literal["read", "read_write"]


def _permissions_for_folder(conn: sqlite3.Connection, folder_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT fp.access, fu.username
        FROM folder_permissions fp
        JOIN file_users fu ON fu.id = fp.file_user_id
        WHERE fp.shared_folder_id = ?
        ORDER BY fu.username
        """,
        (folder_id,),
    ).fetchall()
    return [{"username": row["username"], "access": row["access"]} for row in rows]


def _permissions_summary(conn: sqlite3.Connection, folder_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT fp.file_user_id, fu.username, fp.access
        FROM folder_permissions fp
        JOIN file_users fu ON fu.id = fp.file_user_id
        WHERE fp.shared_folder_id = ?
        ORDER BY fu.username
        """,
        (folder_id,),
    ).fetchall()
    return [
        {"user_id": row["file_user_id"], "username": row["username"], "access": row["access"]}
        for row in rows
    ]


def sync_folder_to_system(
    conn: sqlite3.Connection,
    folder_id: int,
    *,
    folder_name: str | None = None,
    folder_path: Path | str | None = None,
) -> None:
    row = conn.execute(
        "SELECT name, path FROM shared_folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

    name = folder_name or row["name"]
    path = Path(folder_path or row["path"])
    perms = _permissions_for_folder(conn, folder_id)
    usernames = [p["username"] for p in perms]

    try:
        samba_shares.write_share_config(name, path, usernames)
        acl.sync_shared_folder_acl(path, [(p["username"], p["access"]) for p in perms])
        samba_shares.test_and_reload()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def replace_folder_permissions(
    folder_id: int,
    entries: list[dict],
) -> list[dict]:
    """Replace all permissions for a folder. entries: [{user_id, access}]."""
    with connect() as conn:
        folder = conn.execute(
            "SELECT id FROM shared_folders WHERE id = ?", (folder_id,)
        ).fetchone()
        if folder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        conn.execute("DELETE FROM folder_permissions WHERE shared_folder_id = ?", (folder_id,))

        for entry in entries:
            user_id = entry["user_id"]
            access = entry["access"]
            if access not in ("read", "read_write"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access must be 'read' or 'read_write'.",
                )
            user = conn.execute(
                "SELECT id FROM file_users WHERE id = ?", (user_id,)
            ).fetchone()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User id {user_id} not found.",
                )
            conn.execute(
                """
                INSERT INTO folder_permissions (file_user_id, shared_folder_id, access)
                VALUES (?, ?, ?)
                """,
                (user_id, folder_id, access),
            )

        sync_folder_to_system(conn, folder_id)
        return _permissions_summary(conn, folder_id)


def replace_user_permissions(
    user_id: int,
    entries: list[dict],
) -> list[dict]:
    """Replace all folder permissions for a user. entries: [{folder_id, access}]."""
    with connect() as conn:
        user = conn.execute("SELECT id FROM file_users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        affected_folders: set[int] = set()
        rows = conn.execute(
            "SELECT shared_folder_id FROM folder_permissions WHERE file_user_id = ?",
            (user_id,),
        ).fetchall()
        affected_folders.update(row["shared_folder_id"] for row in rows)

        conn.execute("DELETE FROM folder_permissions WHERE file_user_id = ?", (user_id,))

        for entry in entries:
            folder_id = entry["folder_id"]
            access = entry["access"]
            if access not in ("read", "read_write"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access must be 'read' or 'read_write'.",
                )
            folder = conn.execute(
                "SELECT id FROM shared_folders WHERE id = ?", (folder_id,)
            ).fetchone()
            if folder is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Folder id {folder_id} not found.",
                )
            conn.execute(
                """
                INSERT INTO folder_permissions (file_user_id, shared_folder_id, access)
                VALUES (?, ?, ?)
                """,
                (user_id, folder_id, access),
            )
            affected_folders.add(folder_id)

        for folder_id in affected_folders:
            sync_folder_to_system(conn, folder_id)

        rows = conn.execute(
            """
            SELECT fp.shared_folder_id AS folder_id, sf.name AS folder_name, fp.access
            FROM folder_permissions fp
            JOIN shared_folders sf ON sf.id = fp.shared_folder_id
            WHERE fp.file_user_id = ?
            ORDER BY sf.name
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
