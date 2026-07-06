#!/usr/bin/env python3
"""On-appliance demo seed — clears file users/folders and loads hire & sales data."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from frogswork_api.db import connect, init_db
from frogswork_api.services import archetypes as archetype_service
from frogswork_api.services import folders as folder_service
from frogswork_api.services import users as user_service

FOLDERS = [
    "Equipment Hire",
    "Sales Quotes",
    "Customer Files",
    "Marketing Assets",
    "Accounts Admin",
]

ARCHETYPES = {
    "Sales Team": {
        "Equipment Hire": "read",
        "Sales Quotes": "read_write",
        "Customer Files": "read",
        "Marketing Assets": "read",
    },
    "Yard & Dispatch": {
        "Equipment Hire": "read_write",
        "Sales Quotes": "read",
        "Customer Files": "read",
    },
    "Office Manager": {
        "Accounts Admin": "read_write",
        "Sales Quotes": "read_write",
        "Customer Files": "read_write",
        "Equipment Hire": "read",
        "Marketing Assets": "read_write",
    },
}

USERS = [
    ("sarah", "Sarah Chen (Owner)", "sarah-hire-pass", "Super User"),
    ("mike", "Mike Torres (Sales)", "mike-hire-pass", "Sales Team"),
    ("jemma", "Jemma Walsh (Yard)", "jemma-hire-pass", "Yard & Dispatch"),
    ("tina", "Tina Brooks (Office)", "tina-hire-pass", "Office Manager"),
    ("alex", "Alex Nguyen (Trainee)", "alex-hire-pass", "Standard Employee"),
]


def clear_data() -> None:
    with connect() as conn:
        users = conn.execute("SELECT id, username FROM file_users").fetchall()
        archetypes = conn.execute(
            "SELECT id, name, is_system FROM archetypes"
        ).fetchall()
        folders = conn.execute("SELECT id, name, path FROM shared_folders").fetchall()

    for row in users:
        print(f"  delete user {row['username']}")
        user_service.delete_user(row["id"])

    with connect() as conn:
        for row in archetypes:
            if row["is_system"]:
                conn.execute(
                    "DELETE FROM archetype_folder_permissions WHERE archetype_id = ?",
                    (row["id"],),
                )
                continue
            print(f"  delete archetype {row['name']}")
            conn.execute("DELETE FROM archetypes WHERE id = ?", (row["id"],))

    for row in folders:
        path = Path(row["path"])
        if path.exists():
            for child in path.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        print(f"  delete folder {row['name']}")
        folder_service.delete_folder(row["id"])


def seed_data() -> None:
    folder_ids: dict[str, int] = {}
    for name in FOLDERS:
        created = folder_service.create_folder(name=name)
        folder_ids[name] = created["id"]
        print(f"  folder {name}")

    with connect() as conn:
        archetype_service.ensure_system_archetypes(conn)
        existing = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM archetypes").fetchall()
        }

    archetype_ids: dict[str, int] = dict(existing)
    for name in ARCHETYPES:
        if name not in archetype_ids:
            created = archetype_service.create_archetype(name)
            archetype_ids[name] = created["id"]
            print(f"  archetype {name}")

    for name, perms in ARCHETYPES.items():
        entries = [
            {"folder_id": folder_ids[folder_name], "access": access}
            for folder_name, access in perms.items()
        ]
        archetype_service.replace_archetype_permissions(archetype_ids[name], entries)
        print(f"  permissions for {name}")

    for username, display_name, password, archetype_name in USERS:
        with connect() as conn:
            archetype_id = conn.execute(
                "SELECT id FROM archetypes WHERE name = ?", (archetype_name,)
            ).fetchone()["id"]
        user_service.create_user(
            username=username,
            display_name=display_name,
            password=password,
            archetype_id=archetype_id,
        )
        print(f"  user {username} ({archetype_name})")


def main() -> int:
    print("==> Initialising database")
    init_db()
    print("==> Clearing existing demo data")
    clear_data()
    print("==> Seeding hire & sales business")
    seed_data()
    print("==> Done")
    print("Users: sarah, mike, jemma, tina, alex")
    print("Passwords: {username}-hire-pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
