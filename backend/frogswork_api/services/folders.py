"""Shared folder CRUD and listing."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

from fastapi import HTTPException, status

from frogswork_api.db import connect, utc_now_iso
from frogswork_api.integrations import linux_users, share_layout
from frogswork_api.integrations._run import IntegrationError, run_cmd
from frogswork_api.paths import DATA_FROGSWORK, DATA_SHARED, PERSONAL_CONTAINER_NAME, SAMBA_SHARE_NAME
from frogswork_api.services import permissions as permission_service
from frogswork_api.services import archetypes as archetype_service

FOLDER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")
RESERVED_FOLDER_NAMES = frozenset({PERSONAL_CONTAINER_NAME.lower()})


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip()).strip("-").lower()
    return slug or "folder"


def _folder_entry_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for _ in path.iterdir())


def validate_folder_name(name: str) -> str:
    cleaned = name.strip()
    if not FOLDER_NAME_PATTERN.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder name must be 1–64 characters: letters, digits, spaces, hyphen, underscore.",
        )
    if cleaned.lower() in RESERVED_FOLDER_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The folder name '{cleaned}' is reserved.",
        )
    with connect() as conn:
        user = conn.execute(
            "SELECT id FROM file_users WHERE username = ? COLLATE NOCASE",
            (cleaned.lower(),),
        ).fetchone()
        if user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Folder name '{cleaned}' matches an existing user account.",
            )
    return cleaned


def _row_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "path": row["path"],
        "share_name": SAMBA_SHARE_NAME,
        "quota_bytes": row["quota_bytes"],
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


def create_folder(
    name: str,
    quota_bytes: int | None = None,
    archetype_permissions: list[dict] | None = None,
) -> dict:
    name = validate_folder_name(name)
    if quota_bytes is not None and quota_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage cap must be a positive number of bytes.",
        )
    slug = _slugify(name)
    folder_path = DATA_SHARED / name
    now = utc_now_iso()

    if folder_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A folder named '{name}' already exists on disk.",
        )

    if os.environ.get("FROGSWORK_SKIP_SYSTEM") != "1":
        try:
            run_cmd("test", "!", "-e", str(folder_path))
        except IntegrationError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A folder named '{name}' already exists on disk.",
            ) from None

    folder_id: int | None = None
    try:
        with connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO shared_folders (name, slug, path, quota_bytes, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, slug, str(folder_path), quota_bytes, now),
                )
                folder_id = cursor.lastrowid
            except sqlite3.IntegrityError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Folder '{name}' already exists.",
                ) from exc

        share_layout.create_shared_folder_directory(folder_path)
        if quota_bytes is not None:
            linux_users.set_path_quota(folder_path, quota_bytes)
        with connect() as conn:
            if archetype_permissions:
                archetype_service.apply_folder_archetype_permissions(
                    conn, folder_id, archetype_permissions
                )
            permission_service.sync_folder_to_system(conn, folder_id)
            return get_folder(conn, folder_id)
    except HTTPException:
        raise
    except IntegrationError as exc:
        if folder_id is not None:
            with connect() as conn:
                conn.execute("DELETE FROM shared_folders WHERE id = ?", (folder_id,))
        try:
            share_layout.remove_shared_folder_directory(folder_path)
        except IntegrationError:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception:
        if folder_id is not None:
            with connect() as conn:
                conn.execute("DELETE FROM shared_folders WHERE id = ?", (folder_id,))
        try:
            share_layout.remove_shared_folder_directory(folder_path)
        except IntegrationError:
            pass
        raise


def update_folder(
    folder_id: int,
    *,
    new_name: str | None = None,
    quota_bytes: int | None = None,
    update_quota: bool = False,
) -> dict:
    with connect() as conn:
        folder = get_folder(conn, folder_id)

    if new_name is not None and new_name != folder["name"]:
        return rename_folder(folder_id, new_name)

    if update_quota:
        if quota_bytes is not None and quota_bytes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Storage cap must be a positive number of bytes.",
            )
        path = Path(folder["path"])
        try:
            if quota_bytes is not None:
                linux_users.set_path_quota(path, quota_bytes)
        except IntegrationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        with connect() as conn:
            conn.execute(
                "UPDATE shared_folders SET quota_bytes = ? WHERE id = ?",
                (quota_bytes, folder_id),
            )
            return get_folder(conn, folder_id)

    return folder


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
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not rename folder on disk: {exc}",
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
        entry_count = _folder_entry_count(path)
        if entry_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Folder is not empty ({entry_count} item(s) including hidden files). "
                    "Remove all files and subfolders before deleting."
                ),
            )

    try:
        if path.exists():
            share_layout.remove_shared_folder_directory(path)
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Could not remove folder from disk: {exc}. Ensure it is empty.",
        ) from exc

    with connect() as conn:
        conn.execute("DELETE FROM shared_folders WHERE id = ?", (folder_id,))


def sync_all_folders() -> None:
    """Write ACL state for every shared folder (e.g. after upgrade)."""
    with connect() as conn:
        rows = conn.execute("SELECT id FROM shared_folders").fetchall()
        for row in rows:
            try:
                permission_service.sync_folder_to_system(conn, row["id"])
            except HTTPException:
                pass
