"""Time-limited per-folder and per-person access grants."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from frogswork_api.db import connect, utc_now_iso
from frogswork_api.integrations import linux_users, share_layout
from frogswork_api.integrations._run import IntegrationError
from frogswork_api.services import permissions as permission_service

MAX_ELEVATION_HOURS = 720  # 30 days
ACCESS_RANK = {"none": 0, "read": 1, "read_write": 2}
ACCESS_LEVELS = ("read", "read_write")


def _allowed_access_levels(baseline: str) -> list[str]:
    base_rank = ACCESS_RANK.get(baseline, 0)
    return [level for level in ACCESS_LEVELS if ACCESS_RANK[level] > base_rank]


def _shared_folder_baseline(conn: sqlite3.Connection, user_id: int, folder_id: int) -> str:
    row = conn.execute(
        """
        SELECT afp.access
        FROM file_users fu
        LEFT JOIN archetype_folder_permissions afp
          ON afp.archetype_id = fu.archetype_id AND afp.shared_folder_id = ?
        WHERE fu.id = ?
        """,
        (folder_id, user_id),
    ).fetchone()
    if row is None or row["access"] is None:
        return "none"
    return row["access"]


def _shared_folder_baseline_detail(
    conn: sqlite3.Connection, user_id: int, folder_id: int
) -> dict:
    row = conn.execute(
        """
        SELECT sf.name AS folder_name, a.name AS archetype_name, afp.access
        FROM file_users fu
        JOIN shared_folders sf ON sf.id = ?
        LEFT JOIN archetypes a ON a.id = fu.archetype_id
        LEFT JOIN archetype_folder_permissions afp
          ON afp.archetype_id = fu.archetype_id AND afp.shared_folder_id = ?
        WHERE fu.id = ?
        """,
        (folder_id, folder_id, user_id),
    ).fetchone()
    if row is None:
        return {"folder_name": "?", "archetype_name": None, "baseline_access": "none"}
    baseline = row["access"] if row["access"] is not None else "none"
    return {
        "folder_name": row["folder_name"],
        "archetype_name": row["archetype_name"],
        "baseline_access": baseline,
    }


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _max_access(current: str | None, new: str) -> str:
    if current is None:
        return new
    if ACCESS_RANK[new] > ACCESS_RANK[current]:
        return new
    return current


def archetype_grants_superuser(conn: sqlite3.Connection, user_id: int) -> bool:
    row = conn.execute(
        """
        SELECT a.can_view_all_personal
        FROM file_users fu
        LEFT JOIN archetypes a ON a.id = fu.archetype_id
        WHERE fu.id = ?
        """,
        (user_id,),
    ).fetchone()
    if row is None:
        return False
    return bool(row["can_view_all_personal"])


def list_active_grants(conn: sqlite3.Connection, grantee_user_id: int) -> list[sqlite3.Row]:
    now = utc_now_iso()
    rows = conn.execute(
        """
        SELECT * FROM user_elevation_grants
        WHERE grantee_user_id = ? AND expires_at > ?
        ORDER BY grant_type, target_id
        """,
        (grantee_user_id, now),
    ).fetchall()
    return list(rows)


def _grant_dict(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    if row["grant_type"] == "shared_folder":
        target = conn.execute(
            "SELECT name FROM shared_folders WHERE id = ?", (row["target_id"],)
        ).fetchone()
        target_name = target["name"] if target else "?"
    else:
        target = conn.execute(
            "SELECT username FROM file_users WHERE id = ?", (row["target_id"],)
        ).fetchone()
        target_name = f"Personal/{target['username']}" if target else "?"
    return {
        "grant_type": row["grant_type"],
        "target_id": row["target_id"],
        "target_name": target_name,
        "access": row["access"],
    }


def elevation_summary(conn: sqlite3.Connection, grantee_user_id: int) -> dict | None:
    grants = list_active_grants(conn, grantee_user_id)
    if not grants:
        return None
    first = grants[0]
    return {
        "expires_at": first["expires_at"],
        "granted_at": first["granted_at"],
        "reason": first["reason"],
        "grants": [_grant_dict(conn, row) for row in grants],
    }


def has_active_grants(conn: sqlite3.Connection, grantee_user_id: int) -> bool:
    return elevation_summary(conn, grantee_user_id) is not None


def elevation_options(conn: sqlite3.Connection, grantee_user_id: int) -> dict:
    user = conn.execute(
        "SELECT id FROM file_users WHERE id = ?", (grantee_user_id,)
    ).fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if archetype_grants_superuser(conn, grantee_user_id):
        return {"shared_folders": [], "personal_folders": []}

    shared_folders: list[dict] = []
    for folder in conn.execute(
        "SELECT id, name FROM shared_folders ORDER BY name COLLATE NOCASE"
    ).fetchall():
        baseline = _shared_folder_baseline(conn, grantee_user_id, folder["id"])
        allowed = _allowed_access_levels(baseline)
        if allowed:
            shared_folders.append(
                {
                    "id": folder["id"],
                    "name": folder["name"],
                    "baseline_access": baseline,
                    "allowed_access": allowed,
                }
            )

    personal_folders: list[dict] = []
    for other in conn.execute(
        """
        SELECT id, username, display_name
        FROM file_users
        WHERE id != ?
        ORDER BY display_name COLLATE NOCASE
        """,
        (grantee_user_id,),
    ).fetchall():
        baseline = "none"
        personal_folders.append(
            {
                "user_id": other["id"],
                "username": other["username"],
                "display_name": other["display_name"],
                "baseline_access": baseline,
                "allowed_access": _allowed_access_levels(baseline),
            }
        )

    return {"shared_folders": shared_folders, "personal_folders": personal_folders}


def get_elevation_options(user_id: int) -> dict:
    with connect() as conn:
        return elevation_options(conn, user_id)


def active_shared_grants_for_folder(
    conn: sqlite3.Connection, folder_id: int
) -> list[dict]:
    now = utc_now_iso()
    rows = conn.execute(
        """
        SELECT g.access, fu.username
        FROM user_elevation_grants g
        JOIN file_users fu ON fu.id = g.grantee_user_id
        WHERE g.grant_type = 'shared_folder'
          AND g.target_id = ?
          AND g.expires_at > ?
        """,
        (folder_id, now),
    ).fetchall()
    return [{"username": row["username"], "access": row["access"]} for row in rows]


def merge_folder_permissions(
    base: list[dict], elevation: list[dict]
) -> list[tuple[str, str]]:
    merged: dict[str, str] = {p["username"]: p["access"] for p in base}
    for entry in elevation:
        username = entry["username"]
        merged[username] = _max_access(merged.get(username), entry["access"])
    return [(username, access) for username, access in merged.items()]


def active_personal_grants_for_owner(
    conn: sqlite3.Connection, owner_user_id: int
) -> list[dict]:
    now = utc_now_iso()
    rows = conn.execute(
        """
        SELECT g.access, fu.username AS grantee_username
        FROM user_elevation_grants g
        JOIN file_users fu ON fu.id = g.grantee_user_id
        WHERE g.grant_type = 'personal_folder'
          AND g.target_id = ?
          AND g.expires_at > ?
        """,
        (owner_user_id, now),
    ).fetchall()
    return [dict(row) for row in rows]


def sync_personal_folder_acl(conn: sqlite3.Connection, owner_user_id: int) -> None:
    owner = conn.execute(
        "SELECT username FROM file_users WHERE id = ?", (owner_user_id,)
    ).fetchone()
    if owner is None:
        return
    username = owner["username"]
    extra = [
        (row["grantee_username"], row["access"])
        for row in active_personal_grants_for_owner(conn, owner_user_id)
    ]
    try:
        linux_users.apply_private_folder_permissions(username, extra_grants=extra)
    except IntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def sync_grantee_effects(conn: sqlite3.Connection, grantee_user_id: int) -> None:
    """Re-sync ACLs affected by a grantee's active temporary grants."""
    folder_ids = {
        row["target_id"]
        for row in list_active_grants(conn, grantee_user_id)
        if row["grant_type"] == "shared_folder"
    }
    for folder_id in conn.execute("SELECT id FROM shared_folders").fetchall():
        if folder_id["id"] in folder_ids:
            permission_service.sync_folder_to_system(conn, folder_id["id"])

    owner_ids = {
        row["target_id"]
        for row in list_active_grants(conn, grantee_user_id)
        if row["grant_type"] == "personal_folder"
    }
    for owner_id in owner_ids:
        sync_personal_folder_acl(conn, owner_id)

    share_layout.sync_all_layout_acls(conn)


def expire_stale_elevations(conn: sqlite3.Connection) -> int:
    now = utc_now_iso()
    rows = conn.execute(
        """
        SELECT DISTINCT grantee_user_id, grant_type, target_id
        FROM user_elevation_grants
        WHERE expires_at <= ?
        """,
        (now,),
    ).fetchall()
    if not rows:
        return 0

    affected_grantees = {
        row["grantee_user_id"] for row in conn.execute(
            "SELECT DISTINCT grantee_user_id FROM user_elevation_grants WHERE expires_at <= ?",
            (now,),
        ).fetchall()
    }
    affected_shared = {
        row["target_id"]
        for row in rows
        if row["grant_type"] == "shared_folder"
    }
    affected_owners = {
        row["target_id"]
        for row in rows
        if row["grant_type"] == "personal_folder"
    }

    conn.execute("DELETE FROM user_elevation_grants WHERE expires_at <= ?", (now,))

    for folder_id in affected_shared:
        permission_service.sync_folder_to_system(conn, folder_id)
    for owner_id in affected_owners:
        sync_personal_folder_acl(conn, owner_id)
    for grantee_id in affected_grantees:
        sync_grantee_effects(conn, grantee_id)

    return len(rows)


def _validate_grants(
    conn: sqlite3.Connection,
    grantee_user_id: int,
    grants: list[dict],
) -> list[dict]:
    if not grants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose at least one folder or personal folder to grant access to.",
        )

    if archetype_grants_superuser(conn, grantee_user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super User archetype already has full access; temporary grants are not needed.",
        )

    cleaned: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for grant in grants:
        grant_type = grant["grant_type"]
        target_id = grant["target_id"]
        access = grant["access"]
        if grant_type not in ("shared_folder", "personal_folder"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid grant type.")
        if access not in ("read", "read_write"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access level.")
        key = (grant_type, target_id)
        if key in seen:
            continue
        seen.add(key)

        if grant_type == "shared_folder":
            folder = conn.execute(
                "SELECT id FROM shared_folders WHERE id = ?", (target_id,)
            ).fetchone()
            if folder is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Shared folder id {target_id} not found.",
                )
            detail = _shared_folder_baseline_detail(conn, grantee_user_id, target_id)
            baseline = detail["baseline_access"]
            if ACCESS_RANK[access] <= ACCESS_RANK[baseline]:
                archetype_hint = (
                    f" via {detail['archetype_name']} archetype"
                    if detail["archetype_name"]
                    else ""
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Temporary access must exceed archetype access for "
                        f"'{detail['folder_name']}'{archetype_hint} "
                        f"(current: {baseline.replace('_', ' ')})."
                    ),
                )
        else:
            owner = conn.execute(
                "SELECT id, username FROM file_users WHERE id = ?", (target_id,)
            ).fetchone()
            if owner is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User id {target_id} not found.",
                )
            if owner["id"] == grantee_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot grant temporary access to your own personal folder.",
                )

        cleaned.append(
            {"grant_type": grant_type, "target_id": target_id, "access": access}
        )

    return cleaned


def replace_elevations(
    user_id: int,
    *,
    duration_hours: int,
    reason: str | None,
    grants: list[dict],
) -> dict:
    if duration_hours < 1 or duration_hours > MAX_ELEVATION_HOURS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duration must be between 1 and {MAX_ELEVATION_HOURS} hours.",
        )

    now = datetime.now(UTC)
    expires_at = (now + timedelta(hours=duration_hours)).replace(microsecond=0).isoformat()
    granted_at = utc_now_iso()

    with connect() as conn:
        user = conn.execute(
            "SELECT id, username FROM file_users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        expire_stale_elevations(conn)

        previous_owners = {
            row["target_id"]
            for row in conn.execute(
                """
                SELECT target_id FROM user_elevation_grants
                WHERE grantee_user_id = ? AND grant_type = 'personal_folder'
                """,
                (user_id,),
            ).fetchall()
        }
        previous_shared = {
            row["target_id"]
            for row in conn.execute(
                """
                SELECT target_id FROM user_elevation_grants
                WHERE grantee_user_id = ? AND grant_type = 'shared_folder'
                """,
                (user_id,),
            ).fetchall()
        }

        cleaned = _validate_grants(conn, user_id, grants)

        conn.execute(
            "DELETE FROM user_elevation_grants WHERE grantee_user_id = ?",
            (user_id,),
        )
        for grant in cleaned:
            conn.execute(
                """
                INSERT INTO user_elevation_grants (
                    grantee_user_id, grant_type, target_id, access,
                    expires_at, granted_at, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    grant["grant_type"],
                    grant["target_id"],
                    grant["access"],
                    expires_at,
                    granted_at,
                    reason,
                ),
            )

        affected_shared = previous_shared | {
            g["target_id"] for g in cleaned if g["grant_type"] == "shared_folder"
        }
        affected_owners = previous_owners | {
            g["target_id"] for g in cleaned if g["grant_type"] == "personal_folder"
        }

        for folder_id in affected_shared:
            permission_service.sync_folder_to_system(conn, folder_id)
        for owner_id in affected_owners:
            sync_personal_folder_acl(conn, owner_id)
        share_layout.sync_all_layout_acls(conn)

        summary = elevation_summary(conn, user_id)
        return summary or {}


def revoke_elevations(user_id: int) -> None:
    with connect() as conn:
        user = conn.execute(
            "SELECT id FROM file_users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        grants = list_active_grants(conn, user_id)
        if not grants:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active temporary access for this user.",
            )

        shared_ids = {
            row["target_id"] for row in grants if row["grant_type"] == "shared_folder"
        }
        owner_ids = {
            row["target_id"] for row in grants if row["grant_type"] == "personal_folder"
        }

        conn.execute(
            "DELETE FROM user_elevation_grants WHERE grantee_user_id = ?",
            (user_id,),
        )

        for folder_id in shared_ids:
            permission_service.sync_folder_to_system(conn, folder_id)
        for owner_id in owner_ids:
            sync_personal_folder_acl(conn, owner_id)
        share_layout.sync_all_layout_acls(conn)
