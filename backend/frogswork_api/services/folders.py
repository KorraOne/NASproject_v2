"""Shared folder CRUD and listing."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from fastapi import HTTPException, status

from frogswork_api.db import connect, utc_now_iso
from frogswork_api.integrations import samba_shares
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.paths import DATA_SHARED
from frogswork_api.services import permissions as permission_service

FOLDER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "folder"


def validate_folder_name(name: str) -> str:
    cleaned = name.strip()
    if not FOLDER_NAME_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name must be 1–64 characters: letters, digits, spaces, hyphen, underscore.",
        )
    return cleaned


def _row_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "path": row["path"],
        "share_name": samba_shares.share_name(row["name"]),
        "created_at": row["created_at"],
        "permissions": permission_service._permissions_summary(conn, row["id"]),
    }


def list_folders(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM shared_folders ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return [_row_to_dict(conn, row) for row in rows]


def get_folder(conn: sqlite3.Connection, folder_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM shared_folders WHERE id = ?", (folder_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")
    return _row_to_dict(conn, row)


def create_folder(name: str) -> dict:
    name = validate_folder_name(name)
    slug = _slugify(name)
    folder_path = DATA_SHARED / name
    now = utc_now_iso()

    if folder_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{name}' already exists on disk.",
        )

    folder_id: int | None = None
    try:
        with connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO shared_folders (name, slug, path, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, slug, str(folder_path), now),
                )
                folder_id = cursor.lastrowid
            except sqlite3.IntegrityError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Folder '{name}' already exists.",
                ) from exc

        folder_path.mkdir(parents=True, exist_ok=False)
        with connect() as conn:
            permission_service.sync_folder_to_system(conn, folder_id)
            return get_folder(conn, folder_id)
    except HTTPException:
        raise
    except Exception:
        if folder_id is not None:
            with connect() as conn:
                conn.execute("DELETE FROM shared_folders WHERE id = ?", (folder_id,))
        if folder_path.exists():
            folder_path.rmdir()
        raise


def rename_folder(folder_id: int, new_name: str) -> dict:
    new_name = validate_folder_name(new_name)
    with connect() as conn:
        folder = get_folder(conn, folder_id)
    old_name = folder["name"]
    if old_name == new_name:
        return folder

    old_path = Path(folder["path"])
    new_path = DATA_SHARED / new_name
    if new_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{new_name}' already exists on disk.",
        )

    new_slug = _slugify(new_name)
    try:
        old_path.rename(new_path)
        samba_shares.remove_share_config(old_name)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not rename folder on disk: {exc}",
        ) from exc
    except IntegrationError as exc:
        if new_path.exists() and not old_path.exists():
            new_path.rename(old_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    with connect() as conn:
        try:
            conn.execute(
                """
                UPDATE shared_folders
                SET name = ?, slug = ?, path = ?
                WHERE id = ?
                """,
                (new_name, new_slug, str(new_path), folder_id),
            )
        except sqlite3.IntegrityError as exc:
            if new_path.exists() and not old_path.exists():
                new_path.rename(old_path)
            samba_shares.write_share_config(
                old_name,
                old_path,
                [p["username"] for p in folder["permissions"]],
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Folder '{new_name}' already exists.",
            ) from exc
        permission_service.sync_folder_to_system(conn, folder_id)
        return get_folder(conn, folder_id)


def delete_folder(folder_id: int) -> None:
    with connect() as conn:
        folder = get_folder(conn, folder_id)
        path = Path(folder["path"])
        if path.exists() and any(path.iterdir()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder is not empty. Remove files before deleting.",
            )

    try:
        samba_shares.remove_share_config(folder["name"])
        if path.exists():
            path.rmdir()
        samba_shares.test_and_reload()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    with connect() as conn:
        conn.execute("DELETE FROM shared_folders WHERE id = ?", (folder_id,))


def sync_all_folders() -> None:
    """Write Samba/ACL state for every shared folder (e.g. after upgrade)."""
    with connect() as conn:
        rows = conn.execute("SELECT id FROM shared_folders").fetchall()
        for row in rows:
            try:
                permission_service.sync_folder_to_system(conn, row["id"])
            except HTTPException:
                pass
