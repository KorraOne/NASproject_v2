#!/usr/bin/env python3
"""Reset demo data and seed a small hire & sales business on FrogsWork."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_PASSWORD = "FrogsWork-Dev-2026"

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
    {
        "username": "sarah",
        "display_name": "Sarah Chen (Owner)",
        "password": "sarah-hire-pass",
        "archetype": "Super User",
    },
    {
        "username": "mike",
        "display_name": "Mike Torres (Sales)",
        "password": "mike-hire-pass",
        "archetype": "Sales Team",
    },
    {
        "username": "jemma",
        "display_name": "Jemma Walsh (Yard)",
        "password": "jemma-hire-pass",
        "archetype": "Yard & Dispatch",
    },
    {
        "username": "tina",
        "display_name": "Tina Brooks (Office)",
        "password": "tina-hire-pass",
        "archetype": "Office Manager",
    },
    {
        "username": "alex",
        "display_name": "Alex Nguyen (Trainee)",
        "password": "alex-hire-pass",
        "archetype": "Standard Employee",
    },
]


class Client:
    def __init__(self, base: str, token: str) -> None:
        self.base = base.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, body: dict | None = None) -> object:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            headers=self.headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            raise RuntimeError(f"{method} {path} failed ({exc.code}): {detail}") from exc


def login(base: str, password: str) -> str:
    payload = json.dumps({"password": password}).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/api/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())["access_token"]


def clear_existing(client: Client) -> None:
    print("==> Removing existing file users")
    for user in client.request("GET", "/api/users"):
        client.request("DELETE", f"/api/users/{user['id']}")
        print(f"    deleted user {user['username']}")

    print("==> Removing custom archetypes")
    for archetype in client.request("GET", "/api/archetypes"):
        if archetype["is_system"]:
            continue
        client.request("DELETE", f"/api/archetypes/{archetype['id']}")
        print(f"    deleted archetype {archetype['name']}")

    print("==> Removing shared folders")
    for folder in client.request("GET", "/api/folders"):
        client.request("DELETE", f"/api/folders/{folder['id']}")
        print(f"    deleted folder {folder['name']}")


def seed_business(client: Client) -> None:
    print("==> Creating shared folders")
    folder_ids: dict[str, int] = {}
    for name in FOLDERS:
        folder = client.request("POST", "/api/folders", {"name": name})
        folder_ids[name] = folder["id"]
        print(f"    {name}")

    print("==> Creating custom archetypes")
    archetype_ids: dict[str, int] = {}
    existing = {a["name"]: a["id"] for a in client.request("GET", "/api/archetypes")}
    for name in ARCHETYPES:
        if name in existing:
            archetype_ids[name] = existing[name]
            continue
        created = client.request("POST", "/api/archetypes", {"name": name})
        archetype_ids[name] = created["id"]
        print(f"    {name}")

    print("==> Setting archetype permissions")
    for name, perms in ARCHETYPES.items():
        payload = {
            "permissions": [
                {"folder_id": folder_ids[folder_name], "access": access}
                for folder_name, access in perms.items()
            ]
        }
        client.request("PUT", f"/api/archetypes/{archetype_ids[name]}/permissions", payload)
        print(f"    {name}: {len(perms)} folders")

    print("==> Creating file users")
    all_archetypes = {
        a["name"]: a["id"] for a in client.request("GET", "/api/archetypes")
    }
    for spec in USERS:
        client.request(
            "POST",
            "/api/users",
            {
                "username": spec["username"],
                "display_name": spec["display_name"],
                "password": spec["password"],
                "archetype_id": all_archetypes[spec["archetype"]],
            },
        )
        print(f"    {spec['username']} -> {spec['archetype']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost", help="Appliance base URL")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Dashboard admin password")
    args = parser.parse_args()

    print(f"==> Logging in to {args.base}")
    token = login(args.base, args.password)
    client = Client(args.base, token)

    clear_existing(client)
    seed_business(client)

    print("==> Demo seed complete")
    print("    Users: sarah (owner), mike, jemma, tina, alex")
    print("    Password pattern: {username}-hire-pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
