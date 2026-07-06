"""SQLite database access and schema."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from frogswork_api.config import get_database_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dashboard_admin (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    password_hash TEXT NOT NULL,
    email TEXT,
    backup_email TEXT,
    backup_phone TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS device_identity (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    serial TEXT NOT NULL UNIQUE,
    claim_code_hash TEXT NOT NULL,
    manufactured_at TEXT NOT NULL,
    software_version TEXT NOT NULL,
    claimed_at TEXT,
    claim_attempts INTEGER NOT NULL DEFAULT 0,
    claim_window_start TEXT
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shared_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL UNIQUE,
    quota_bytes INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    is_superuser INTEGER NOT NULL DEFAULT 0,
    quota_bytes INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS folder_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_user_id INTEGER NOT NULL REFERENCES file_users(id) ON DELETE CASCADE,
    shared_folder_id INTEGER NOT NULL REFERENCES shared_folders(id) ON DELETE CASCADE,
    access TEXT NOT NULL CHECK (access IN ('read', 'read_write')),
    UNIQUE (file_user_id, shared_folder_id)
);

CREATE TABLE IF NOT EXISTS archetypes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_system INTEGER NOT NULL DEFAULT 0,
    can_view_all_personal INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS archetype_folder_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archetype_id INTEGER NOT NULL REFERENCES archetypes(id) ON DELETE CASCADE,
    shared_folder_id INTEGER NOT NULL REFERENCES shared_folders(id) ON DELETE CASCADE,
    access TEXT NOT NULL CHECK (access IN ('read', 'read_write')),
    UNIQUE (archetype_id, shared_folder_id)
);

CREATE TABLE IF NOT EXISTS user_elevation_grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    grantee_user_id INTEGER NOT NULL REFERENCES file_users(id) ON DELETE CASCADE,
    grant_type TEXT NOT NULL CHECK (grant_type IN ('shared_folder', 'personal_folder')),
    target_id INTEGER NOT NULL,
    access TEXT NOT NULL CHECK (access IN ('read', 'read_write')),
    expires_at TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    reason TEXT,
    UNIQUE (grantee_user_id, grant_type, target_id)
);
"""


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def init_db(db_path: Path | None = None) -> None:
    path = db_path or get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(_SCHEMA)
        _migrate_schema(conn)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(shared_folders)").fetchall()
    }
    if "quota_bytes" not in columns:
        conn.execute("ALTER TABLE shared_folders ADD COLUMN quota_bytes INTEGER")

    user_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(file_users)").fetchall()
    }
    if "archetype_id" not in user_columns:
        conn.execute(
            "ALTER TABLE file_users ADD COLUMN archetype_id INTEGER REFERENCES archetypes(id)"
        )

    _migrate_admin_columns(conn)
    _migrate_archetypes(conn)
    _migrate_elevation_grants(conn)


def _migrate_admin_columns(conn: sqlite3.Connection) -> None:
    admin_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(dashboard_admin)").fetchall()
    }
    for column, ddl in (
        ("email", "ALTER TABLE dashboard_admin ADD COLUMN email TEXT"),
        ("backup_email", "ALTER TABLE dashboard_admin ADD COLUMN backup_email TEXT"),
        ("backup_phone", "ALTER TABLE dashboard_admin ADD COLUMN backup_phone TEXT"),
    ):
        if column not in admin_columns:
            conn.execute(ddl)


def _migrate_elevation_grants(conn: sqlite3.Connection) -> None:
    tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "user_elevations" in tables:
        conn.execute("DROP TABLE user_elevations")
    if "user_elevation_grants" not in tables:
        conn.execute(
            """
            CREATE TABLE user_elevation_grants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grantee_user_id INTEGER NOT NULL REFERENCES file_users(id) ON DELETE CASCADE,
                grant_type TEXT NOT NULL CHECK (grant_type IN ('shared_folder', 'personal_folder')),
                target_id INTEGER NOT NULL,
                access TEXT NOT NULL CHECK (access IN ('read', 'read_write')),
                expires_at TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                reason TEXT,
                UNIQUE (grantee_user_id, grant_type, target_id)
            )
            """
        )


def _migrate_archetypes(conn: sqlite3.Connection) -> None:
    from frogswork_api.services.archetypes import (
        STANDARD_EMPLOYEE_NAME,
        SUPER_USER_NAME,
        ensure_system_archetypes,
        get_archetype_by_name,
    )

    ensure_system_archetypes(conn)

    super_row = get_archetype_by_name(conn, SUPER_USER_NAME)
    standard_row = get_archetype_by_name(conn, STANDARD_EMPLOYEE_NAME)
    if super_row is None or standard_row is None:
        return

    rows = conn.execute(
        "SELECT id, is_superuser, archetype_id FROM file_users"
    ).fetchall()
    for row in rows:
        if row["archetype_id"] is not None:
            continue
        archetype_id = super_row["id"] if row["is_superuser"] else standard_row["id"]
        conn.execute(
            "UPDATE file_users SET archetype_id = ? WHERE id = ?",
            (archetype_id, row["id"]),
        )


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    path = db_path or get_database_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_setting(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute(
        "SELECT value FROM system_settings WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return default
    return row["value"]


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO system_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def is_setup_complete(conn: sqlite3.Connection) -> bool:
    return get_setting(conn, "setup_complete", "false") == "true"
