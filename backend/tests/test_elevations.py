"""Temporary per-folder and per-person access tests."""

import os
from datetime import UTC, datetime, timedelta

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_mocks(monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.linux_users.set_superuser_membership",
        lambda u, e: None,
    )
    monkeypatch.setattr(
        "frogswork_api.services.elevations.linux_users.apply_private_folder_permissions",
        lambda u, **kw: None,
    )
    monkeypatch.setattr(
        "frogswork_api.services.elevations.share_layout.sync_all_layout_acls",
        lambda c: None,
    )


def test_grant_shared_folder_elevation(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "elevuser", "password": "elev-pass-1"},
    ).json()

    response = client.put(
        f"/api/users/{user['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 8,
            "reason": "Covering sales",
            "grants": [
                {
                    "grant_type": "shared_folder",
                    "target_id": projects_id,
                    "access": "read_write",
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["grants"]) == 1
    assert body["grants"][0]["target_name"] == "Projects"
    assert body["grants"][0]["access"] == "read_write"

    updated = client.get(f"/api/users/{user['id']}", headers=admin_headers).json()
    assert updated["is_elevated"] is True
    assert updated["is_superuser"] is False


def test_grant_personal_folder_elevation(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    owner = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "ownerx", "password": "owner-pass1"},
    ).json()
    grantee = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "coverx", "password": "cover-pass1"},
    ).json()

    response = client.put(
        f"/api/users/{grantee['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 4,
            "grants": [
                {
                    "grant_type": "personal_folder",
                    "target_id": owner["id"],
                    "access": "read",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["grants"][0]["grant_type"] == "personal_folder"
    assert "ownerx" in response.json()["grants"][0]["target_name"]


def test_cannot_elevate_super_user_archetype(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    archetypes = client.get("/api/archetypes", headers=admin_headers).json()
    super_id = next(a["id"] for a in archetypes if a["name"] == "Super User")
    folders = client.get("/api/folders", headers=admin_headers).json()
    folder_id = folders[0]["id"]

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "superx", "password": "super-pass1", "archetype_id": super_id},
    ).json()

    response = client.put(
        f"/api/users/{user['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 4,
            "grants": [
                {"grant_type": "shared_folder", "target_id": folder_id, "access": "read"}
            ],
        },
    )
    assert response.status_code == 400


def test_elevation_options_excludes_full_access_folders(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    archetypes = client.get("/api/archetypes", headers=admin_headers).json()
    standard_id = next(a["id"] for a in archetypes if a["name"] == "Standard Employee")
    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    client.put(
        f"/api/archetypes/{standard_id}/permissions",
        headers=admin_headers,
        json={
            "permissions": [
                {"folder_id": projects_id, "access": "read_write"},
            ]
        },
    )

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "optsuser",
            "password": "opts-pass-1",
            "archetype_id": standard_id,
        },
    ).json()

    options = client.get(
        f"/api/users/{user['id']}/elevation/options",
        headers=admin_headers,
    ).json()
    project_option = next((f for f in options["shared_folders"] if f["id"] == projects_id), None)
    assert project_option is None

    invoices_id = next(f["id"] for f in folders if f["name"] == "Invoices")
    invoice_option = next(f for f in options["shared_folders"] if f["id"] == invoices_id)
    assert invoice_option["baseline_access"] == "none"
    assert set(invoice_option["allowed_access"]) == {"read", "read_write"}


def test_rejects_same_level_shared_folder_elevation(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    archetypes = client.get("/api/archetypes", headers=admin_headers).json()
    standard_id = next(a["id"] for a in archetypes if a["name"] == "Standard Employee")
    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    client.put(
        f"/api/archetypes/{standard_id}/permissions",
        headers=admin_headers,
        json={
            "permissions": [{"folder_id": projects_id, "access": "read"}],
        },
    )

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "samelevel",
            "password": "same-pass-1",
            "archetype_id": standard_id,
        },
    ).json()

    response = client.put(
        f"/api/users/{user['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 4,
            "grants": [
                {"grant_type": "shared_folder", "target_id": projects_id, "access": "read"}
            ],
        },
    )
    assert response.status_code == 400
    assert "exceed archetype access" in response.json()["detail"].lower()


def test_accepts_upgrade_shared_folder_elevation(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    archetypes = client.get("/api/archetypes", headers=admin_headers).json()
    standard_id = next(a["id"] for a in archetypes if a["name"] == "Standard Employee")
    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    client.put(
        f"/api/archetypes/{standard_id}/permissions",
        headers=admin_headers,
        json={
            "permissions": [{"folder_id": projects_id, "access": "read"}],
        },
    )

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "upgrade",
            "password": "upgrade-pass",
            "archetype_id": standard_id,
        },
    ).json()

    response = client.put(
        f"/api/users/{user['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 4,
            "grants": [
                {
                    "grant_type": "shared_folder",
                    "target_id": projects_id,
                    "access": "read_write",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["grants"][0]["access"] == "read_write"


def test_revoke_elevations(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    folders = client.get("/api/folders", headers=admin_headers).json()
    folder_id = folders[0]["id"]
    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "revoke2", "password": "revoke-pass"},
    ).json()

    client.put(
        f"/api/users/{user['id']}/elevation",
        headers=admin_headers,
        json={
            "duration_hours": 24,
            "grants": [
                {"grant_type": "shared_folder", "target_id": folder_id, "access": "read"}
            ],
        },
    )

    response = client.delete(f"/api/users/{user['id']}/elevation", headers=admin_headers)
    assert response.status_code == 200

    updated = client.get(f"/api/users/{user['id']}", headers=admin_headers).json()
    assert updated["is_elevated"] is False
    assert updated["elevation"] is None


def test_expired_grants_cleared(client, admin_headers, monkeypatch):
    _user_mocks(monkeypatch)

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "expired2", "password": "expired-pass"},
    ).json()

    from frogswork_api.db import connect, utc_now_iso

    past = (datetime.now(UTC) - timedelta(hours=1)).replace(microsecond=0).isoformat()
    folders = client.get("/api/folders", headers=admin_headers).json()
    folder_id = folders[0]["id"]
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO user_elevation_grants (
                grantee_user_id, grant_type, target_id, access,
                expires_at, granted_at, reason
            )
            VALUES (?, 'shared_folder', ?, 'read', ?, ?, ?)
            """,
            (user["id"], folder_id, past, utc_now_iso(), "expired"),
        )

    updated = client.get(f"/api/users/{user['id']}", headers=admin_headers).json()
    assert updated["is_elevated"] is False
