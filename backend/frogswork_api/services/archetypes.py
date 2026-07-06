"""User archetype templates and permission sync."""

from __future__ import annotations

import sqlite3

from fastapi import HTTPException, status

from frogswork_api.db import connect, utc_now_iso
from frogswork_api.integrations import linux_users
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.services import elevations as elevation_service
from frogswork_api.services import permissions as permission_service

SUPER_USER_NAME = "Super User"
STANDARD_EMPLOYEE_NAME = "Standard Employee"


def get_archetype_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM archetypes WHERE name = ?", (name,)).fetchone()


def ensure_system_archetypes(conn: sqlite3.Connection) -> None:
    now = utc_now_iso()
    for name, can_view_all_personal in (
        (SUPER_USER_NAME, True),
        (STANDARD_EMPLOYEE_NAME, False),
    ):
        existing = get_archetype_by_name(conn, name)
        if existing is None:
            conn.execute(
                """
                INSERT INTO archetypes (name, is_system, can_view_all_personal, created_at)
                VALUES (?, 1, ?, ?)
                """,
                (name, int(can_view_all_personal), now),
            )


def get_standard_archetype_id(conn: sqlite3.Connection) -> int:
    ensure_system_archetypes(conn)
    row = get_archetype_by_name(conn, STANDARD_EMPLOYEE_NAME)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Standard Employee archetype is missing.",
        )
    return row["id"]


def _folder_permissions_for_archetype(conn: sqlite3.Connection, archetype_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT afp.shared_folder_id AS folder_id, sf.name AS folder_name, afp.access
        FROM archetype_folder_permissions afp
        JOIN shared_folders sf ON sf.id = afp.shared_folder_id
        WHERE afp.archetype_id = ?
        ORDER BY sf.name
        """,
        (archetype_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _permissions_summary(conn: sqlite3.Connection, archetype_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT afp.shared_folder_id AS folder_id, sf.name AS folder_name, afp.access
        FROM archetype_folder_permissions afp
        JOIN shared_folders sf ON sf.id = afp.shared_folder_id
        WHERE afp.archetype_id = ?
        ORDER BY sf.name
        """,
        (archetype_id,),
    ).fetchall()
    return [
        {
            "folder_id": row["folder_id"],
            "folder_name": row["folder_name"],
            "access": row["access"],
        }
        for row in rows
    ]


def _row_to_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    user_count = conn.execute(
        "SELECT COUNT(*) AS count FROM file_users WHERE archetype_id = ?",
        (row["id"],),
    ).fetchone()["count"]
    return {
        "id": row["id"],
        "name": row["name"],
        "is_system": bool(row["is_system"]),
        "can_view_all_personal": bool(row["can_view_all_personal"]),
        "user_count": user_count,
        "created_at": row["created_at"],
        "folder_permissions": _permissions_summary(conn, row["id"]),
    }


def list_archetypes(conn: sqlite3.Connection) -> list[dict]:
    ensure_system_archetypes(conn)
    rows = conn.execute(
        "SELECT * FROM archetypes ORDER BY is_system DESC, name COLLATE NOCASE"
    ).fetchall()
    return [_row_to_dict(conn, row) for row in rows]


def get_archetype(conn: sqlite3.Connection, archetype_id: int) -> dict:
    ensure_system_archetypes(conn)
    row = conn.execute("SELECT * FROM archetypes WHERE id = ?", (archetype_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archetype not found.")
    return _row_to_dict(conn, row)


def _validate_custom_archetype_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archetype name is required.",
        )
    if cleaned in (SUPER_USER_NAME, STANDARD_EMPLOYEE_NAME):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The name '{cleaned}' is reserved.",
        )
    return cleaned


def create_archetype(name: str) -> dict:
    cleaned = _validate_custom_archetype_name(name)
    now = utc_now_iso()
    with connect() as conn:
        ensure_system_archetypes(conn)
        try:
            cursor = conn.execute(
                """
                INSERT INTO archetypes (name, is_system, can_view_all_personal, created_at)
                VALUES (?, 0, 0, ?)
                """,
                (cleaned, now),
            )
            archetype_id = cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Archetype '{cleaned}' already exists.",
            ) from exc
        return get_archetype(conn, archetype_id)


def update_archetype(archetype_id: int, *, name: str | None = None) -> dict:
    with connect() as conn:
        existing = get_archetype(conn, archetype_id)
        if existing["is_system"]:
            if name is not None and name.strip() != existing["name"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="System archetypes cannot be renamed.",
                )
            return existing

        new_name = existing["name"]
        if name is not None:
            new_name = _validate_custom_archetype_name(name)
        try:
            conn.execute(
                "UPDATE archetypes SET name = ? WHERE id = ?",
                (new_name, archetype_id),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Archetype '{new_name}' already exists.",
            ) from exc
        return get_archetype(conn, archetype_id)


def delete_archetype(archetype_id: int) -> None:
    with connect() as conn:
        existing = get_archetype(conn, archetype_id)
        if existing["is_system"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System archetypes cannot be deleted.",
            )
        if existing["user_count"] > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reassign users before deleting this archetype.",
            )
        conn.execute("DELETE FROM archetypes WHERE id = ?", (archetype_id,))


def replace_archetype_permissions(
    archetype_id: int,
    entries: list[dict],
) -> list[dict]:
    with connect() as conn:
        existing = get_archetype(conn, archetype_id)
        if existing["can_view_all_personal"]:
            pass  # Super User may still have shared folder template entries

        conn.execute(
            "DELETE FROM archetype_folder_permissions WHERE archetype_id = ?",
            (archetype_id,),
        )

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
                INSERT INTO archetype_folder_permissions (archetype_id, shared_folder_id, access)
                VALUES (?, ?, ?)
                """,
                (archetype_id, folder_id, access),
            )

        _sync_users_for_archetype(conn, archetype_id)
        return _permissions_summary(conn, archetype_id)


def folder_archetype_permissions_summary(
    conn: sqlite3.Connection, folder_id: int
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT afp.archetype_id, a.name AS archetype_name, afp.access
        FROM archetype_folder_permissions afp
        JOIN archetypes a ON a.id = afp.archetype_id
        WHERE afp.shared_folder_id = ?
        ORDER BY a.name COLLATE NOCASE
        """,
        (folder_id,),
    ).fetchall()
    return [
        {
            "archetype_id": row["archetype_id"],
            "archetype_name": row["archetype_name"],
            "access": row["access"],
        }
        for row in rows
    ]


def get_folder_archetype_permissions(folder_id: int) -> list[dict]:
    with connect() as conn:
        folder = conn.execute(
            "SELECT id FROM shared_folders WHERE id = ?", (folder_id,)
        ).fetchone()
        if folder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")
        return folder_archetype_permissions_summary(conn, folder_id)


def replace_folder_archetype_permissions(
    folder_id: int,
    entries: list[dict],
) -> list[dict]:
    with connect() as conn:
        folder = conn.execute(
            "SELECT id FROM shared_folders WHERE id = ?", (folder_id,)
        ).fetchone()
        if folder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        old_archetype_ids = {
            row["archetype_id"]
            for row in conn.execute(
                """
                SELECT archetype_id FROM archetype_folder_permissions
                WHERE shared_folder_id = ?
                """,
                (folder_id,),
            ).fetchall()
        }

        conn.execute(
            "DELETE FROM archetype_folder_permissions WHERE shared_folder_id = ?",
            (folder_id,),
        )

        new_archetype_ids: set[int] = set()
        for entry in entries:
            archetype_id = entry["archetype_id"]
            access = entry["access"]
            if access not in ("read", "read_write"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access must be 'read' or 'read_write'.",
                )
            archetype = conn.execute(
                "SELECT id FROM archetypes WHERE id = ?", (archetype_id,)
            ).fetchone()
            if archetype is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Archetype id {archetype_id} not found.",
                )
            conn.execute(
                """
                INSERT INTO archetype_folder_permissions (archetype_id, shared_folder_id, access)
                VALUES (?, ?, ?)
                """,
                (archetype_id, folder_id, access),
            )
            new_archetype_ids.add(archetype_id)

        for archetype_id in old_archetype_ids | new_archetype_ids:
            _sync_users_for_archetype(conn, archetype_id)
        permission_service.sync_folder_to_system(conn, folder_id)
        return folder_archetype_permissions_summary(conn, folder_id)


def apply_folder_archetype_permissions(
    conn: sqlite3.Connection,
    folder_id: int,
    entries: list[dict],
) -> None:
    """Set archetype permissions for a folder within an existing transaction."""
    new_archetype_ids: set[int] = set()
    for entry in entries:
        archetype_id = entry["archetype_id"]
        access = entry["access"]
        if access not in ("read", "read_write"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access must be 'read' or 'read_write'.",
            )
        archetype = conn.execute(
            "SELECT id FROM archetypes WHERE id = ?", (archetype_id,)
        ).fetchone()
        if archetype is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Archetype id {archetype_id} not found.",
            )
        conn.execute(
            """
            INSERT INTO archetype_folder_permissions (archetype_id, shared_folder_id, access)
            VALUES (?, ?, ?)
            """,
            (archetype_id, folder_id, access),
        )
        new_archetype_ids.add(archetype_id)

    for archetype_id in new_archetype_ids:
        _sync_users_for_archetype(conn, archetype_id)


def _sync_users_for_archetype(conn: sqlite3.Connection, archetype_id: int) -> None:
    archetype = get_archetype(conn, archetype_id)
    users = conn.execute(
        "SELECT id, username FROM file_users WHERE archetype_id = ?",
        (archetype_id,),
    ).fetchall()
    entries = _folder_permissions_for_archetype(conn, archetype_id)
    for user in users:
        _apply_archetype_to_user(conn, user["id"], user["username"], archetype, entries)


def _apply_archetype_to_user(
    conn: sqlite3.Connection,
    user_id: int,
    username: str,
    archetype: dict,
    entries: list[dict] | None = None,
) -> None:
    if entries is None:
        entries = _folder_permissions_for_archetype(conn, archetype["id"])

    all_folder_ids = [
        row["id"] for row in conn.execute("SELECT id FROM shared_folders").fetchall()
    ]

    conn.execute("DELETE FROM folder_permissions WHERE file_user_id = ?", (user_id,))
    for entry in entries:
        conn.execute(
            """
            INSERT INTO folder_permissions (file_user_id, shared_folder_id, access)
            VALUES (?, ?, ?)
            """,
            (user_id, entry["folder_id"], entry["access"]),
        )

    try:
        linux_users.set_superuser_membership(username, archetype["can_view_all_personal"])
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    conn.execute(
        "UPDATE file_users SET is_superuser = ?, updated_at = ? WHERE id = ?",
        (int(archetype["can_view_all_personal"]), utc_now_iso(), user_id),
    )

    for folder_id in all_folder_ids:
        permission_service.sync_folder_to_system(conn, folder_id)

    elevation_service.sync_grantee_effects(conn, user_id)


def assign_user_archetype(user_id: int, archetype_id: int) -> None:
    with connect() as conn:
        user = conn.execute(
            "SELECT id, username FROM file_users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        archetype = get_archetype(conn, archetype_id)
        conn.execute(
            "UPDATE file_users SET archetype_id = ?, updated_at = ? WHERE id = ?",
            (archetype_id, utc_now_iso(), user_id),
        )
        _apply_archetype_to_user(conn, user_id, user["username"], archetype)


def apply_archetype_on_user_create(conn: sqlite3.Connection, user_id: int, archetype_id: int) -> None:
    user = conn.execute(
        "SELECT username FROM file_users WHERE id = ?", (user_id,)
    ).fetchone()
    if user is None:
        return
    archetype = get_archetype(conn, archetype_id)
    _apply_archetype_to_user(conn, user_id, user["username"], archetype)


def list_effective_permissions(conn: sqlite3.Connection) -> list[dict]:
    from frogswork_api.services import elevations as elevation_service

    ensure_system_archetypes(conn)
    elevation_service.expire_stale_elevations(conn)
    users = conn.execute(
        """
        SELECT fu.id, fu.username, fu.display_name, fu.archetype_id,
               a.name AS archetype_name, a.can_view_all_personal
        FROM file_users fu
        LEFT JOIN archetypes a ON a.id = fu.archetype_id
        ORDER BY fu.username COLLATE NOCASE
        """
    ).fetchall()

    result: list[dict] = []
    for user in users:
        folder_rows = conn.execute(
            """
            SELECT sf.name AS folder_name, fp.access
            FROM folder_permissions fp
            JOIN shared_folders sf ON sf.id = fp.shared_folder_id
            WHERE fp.file_user_id = ?
            ORDER BY sf.name
            """,
            (user["id"],),
        ).fetchall()
        archetype_super = bool(user["can_view_all_personal"])
        elevation = elevation_service.elevation_summary(conn, user["id"])

        shared_access: dict[str, str] = {
            row["folder_name"]: row["access"] for row in folder_rows
        }
        if elevation:
            for grant in elevation["grants"]:
                if grant["grant_type"] == "shared_folder":
                    name = grant["target_name"]
                    shared_access[name] = elevation_service._max_access(
                        shared_access.get(name), grant["access"]
                    )

        result.append(
            {
                "user_id": user["id"],
                "username": user["username"],
                "display_name": user["display_name"],
                "archetype_id": user["archetype_id"],
                "archetype_name": user["archetype_name"],
                "can_view_all_personal": archetype_super,
                "is_elevated": elevation is not None,
                "elevation": elevation,
                "personal_folder": f"Personal/{user['username']}",
                "shared_folders": [
                    {"folder_name": name, "access": access}
                    for name, access in sorted(shared_access.items())
                ],
            }
        )
    return result
