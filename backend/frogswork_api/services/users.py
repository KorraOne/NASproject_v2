"""File user business logic and system sync."""

from __future__ import annotations

import re
import sqlite3

from fastapi import HTTPException, status

from frogswork_api.db import connect, get_setting, utc_now_iso
from frogswork_api.integrations import linux_users, samba, share_layout
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.services import archetypes as archetype_service
from frogswork_api.services import elevations as elevation_service
from frogswork_api.services import permissions as permission_service
from frogswork_api.services.system import DEFAULT_PERSONAL_QUOTA_KEY

USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,31}$")
MIN_FILE_USER_PASSWORD_LENGTH = 8
RESERVED_USERNAMES = frozenset({"root", "frogswork", "admin", "daemon", "www-data"})


def validate_username(username: str) -> str:
    name = username.strip().lower()
    if name in RESERVED_USERNAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The username '{name}' is reserved.",
        )
    if not USERNAME_PATTERN.match(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3–32 characters: lowercase letters, digits, underscore; start with a letter.",
        )
    return name


def _row_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    elevation_service.expire_stale_elevations(conn)
    archetype_row = None
    if row["archetype_id"] is not None:
        archetype_row = conn.execute(
            "SELECT name, can_view_all_personal FROM archetypes WHERE id = ?",
            (row["archetype_id"],),
        ).fetchone()
    archetype_super = (
        bool(archetype_row["can_view_all_personal"])
        if archetype_row is not None
        else bool(row["is_superuser"])
    )
    elevation = elevation_service.elevation_summary(conn, row["id"])
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "archetype_id": row["archetype_id"],
        "archetype_name": archetype_row["name"] if archetype_row is not None else None,
        "is_superuser": archetype_super,
        "is_elevated": elevation is not None,
        "elevation": elevation,
        "quota_bytes": row["quota_bytes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_users(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM file_users ORDER BY username COLLATE NOCASE"
    ).fetchall()
    return [_row_to_dict(conn, row) for row in rows]


def get_user(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM file_users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _row_to_dict(conn, row)


def _cleanup_system_user(username: str) -> None:
    try:
        samba.delete_user(username)
    except IntegrationError:
        pass
    try:
        linux_users.delete_linux_user(username)
    except IntegrationError:
        pass


def create_user(
    *,
    username: str,
    display_name: str,
    password: str,
    archetype_id: int | None = None,
    quota_bytes: int | None = None,
) -> dict:
    username = validate_username(username)
    if len(password) < MIN_FILE_USER_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_FILE_USER_PASSWORD_LENGTH} characters.",
        )
    if quota_bytes is not None and quota_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quota must be a positive number of bytes.",
        )

    now = utc_now_iso()
    user_id: int | None = None

    with connect() as conn:
        archetype_service.ensure_system_archetypes(conn)
        if archetype_id is None:
            archetype_id = archetype_service.get_standard_archetype_id(conn)
        archetype = archetype_service.get_archetype(conn, archetype_id)
        if quota_bytes is None:
            raw = get_setting(conn, DEFAULT_PERSONAL_QUOTA_KEY)
            if raw is not None:
                quota_bytes = int(raw)

    try:
        with connect() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO file_users (
                        username, display_name, is_superuser, archetype_id,
                        quota_bytes, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        display_name,
                        int(archetype["can_view_all_personal"]),
                        archetype_id,
                        quota_bytes,
                        now,
                        now,
                    ),
                )
                user_id = cursor.lastrowid
            except sqlite3.IntegrityError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{username}' is already taken.",
                ) from exc

        linux_users.create_linux_user(username)
        try:
            samba.set_password(username, password)
            if quota_bytes is not None:
                linux_users.set_quota(username, quota_bytes)
            samba.reload_samba()
            with connect() as conn:
                archetype_service.apply_archetype_on_user_create(conn, user_id, archetype_id)
                share_layout.sync_all_layout_acls(conn)
        except IntegrationError as exc:
            _cleanup_system_user(username)
            with connect() as conn:
                conn.execute("DELETE FROM file_users WHERE id = ?", (user_id,))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

        with connect() as conn:
            return get_user(conn, user_id)
    except HTTPException:
        raise
    except Exception:
        if user_id is not None:
            with connect() as conn:
                conn.execute("DELETE FROM file_users WHERE id = ?", (user_id,))
        _cleanup_system_user(username)
        raise


def update_user(
    user_id: int,
    *,
    display_name: str | None = None,
    password: str | None = None,
    archetype_id: int | None = None,
    quota_bytes: int | None = None,
    update_quota: bool = False,
) -> dict:
    with connect() as conn:
        existing = get_user(conn, user_id)
    username = existing["username"]

    if password is not None and len(password) < MIN_FILE_USER_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {MIN_FILE_USER_PASSWORD_LENGTH} characters.",
        )
    if update_quota and quota_bytes is not None and quota_bytes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quota must be a positive number of bytes.",
        )

    now = utc_now_iso()
    new_display = display_name if display_name is not None else existing["display_name"]
    new_quota = quota_bytes if update_quota else existing["quota_bytes"]

    try:
        if password is not None:
            samba.set_password(username, password)
        if update_quota:
            linux_users.set_quota(username, quota_bytes)
        if password is not None:
            samba.reload_samba()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    with connect() as conn:
        conn.execute(
            """
            UPDATE file_users
            SET display_name = ?, quota_bytes = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_display, new_quota, now, user_id),
        )
        if archetype_id is not None and archetype_id != existing["archetype_id"]:
            archetype_service.assign_user_archetype(user_id, archetype_id)
        return get_user(conn, user_id)


def delete_user(user_id: int) -> None:
    with connect() as conn:
        existing = get_user(conn, user_id)
        username = existing["username"]
        affected_folders = [
            row["shared_folder_id"]
            for row in conn.execute(
                "SELECT shared_folder_id FROM folder_permissions WHERE file_user_id = ?",
                (user_id,),
            ).fetchall()
        ]

    try:
        samba.delete_user(username)
        linux_users.delete_linux_user(username)
        samba.reload_samba()
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    with connect() as conn:
        conn.execute("DELETE FROM file_users WHERE id = ?", (user_id,))
        for folder_id in affected_folders:
            permission_service.sync_folder_to_system(conn, folder_id)
        share_layout.sync_all_layout_acls(conn)
