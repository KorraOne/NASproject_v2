"""Archetype API tests."""

import os

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_system_archetypes(client, admin_headers):
    response = client.get("/api/archetypes", headers=admin_headers)
    assert response.status_code == 200
    names = {a["name"] for a in response.json()}
    assert "Super User" in names
    assert "Standard Employee" in names
    super_user = next(a for a in response.json() if a["name"] == "Super User")
    assert super_user["is_system"] is True
    assert super_user["can_view_all_personal"] is True


def test_create_custom_archetype(client, admin_headers):
    response = client.post(
        "/api/archetypes",
        headers=admin_headers,
        json={"name": "Accountant"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Accountant"
    assert body["is_system"] is False
    assert body["can_view_all_personal"] is False


def test_cannot_create_reserved_archetype_name(client, admin_headers):
    response = client.post(
        "/api/archetypes",
        headers=admin_headers,
        json={"name": "Super User"},
    )
    assert response.status_code == 400


def test_user_gets_standard_archetype_by_default(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)

    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "erin", "password": "erin-pass-1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["archetype_name"] == "Standard Employee"
    assert body["is_superuser"] is False


def test_assign_super_user_archetype(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.linux_users.set_superuser_membership",
        lambda u, e: None,
    )
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.elevation_service.sync_grantee_effects",
        lambda c, u: None,
    )

    archetypes = client.get("/api/archetypes", headers=admin_headers).json()
    super_id = next(a["id"] for a in archetypes if a["name"] == "Super User")

    created = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "frank", "password": "frank-pass-1", "archetype_id": super_id},
    ).json()
    assert created["is_superuser"] is True
    assert created["archetype_name"] == "Super User"


def test_archetype_permissions_sync_to_users(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.linux_users.set_superuser_membership",
        lambda u, e: None,
    )
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.elevation_service.sync_grantee_effects",
        lambda c, u: None,
    )

    archetype = client.post(
        "/api/archetypes",
        headers=admin_headers,
        json={"name": "Projects Team"},
    ).json()
    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    client.put(
        f"/api/archetypes/{archetype['id']}/permissions",
        headers=admin_headers,
        json={"permissions": [{"folder_id": projects_id, "access": "read_write"}]},
    )

    user = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "gina",
            "password": "gina-pass-1",
            "archetype_id": archetype["id"],
        },
    ).json()

    folder = client.get(f"/api/folders/{projects_id}", headers=admin_headers).json()
    perms = {p["username"]: p["access"] for p in folder["permissions"]}
    assert perms == {"gina": "read_write"}


def test_effective_permissions(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.linux_users.set_superuser_membership",
        lambda u, e: None,
    )
    monkeypatch.setattr(
        "frogswork_api.services.archetypes.elevation_service.sync_grantee_effects",
        lambda c, u: None,
    )

    client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "helen", "password": "helen-pass-1"},
    )

    response = client.get("/api/permissions/effective", headers=admin_headers)
    assert response.status_code == 200
    helen = next(u for u in response.json() if u["username"] == "helen")
    assert helen["archetype_name"] == "Standard Employee"
    assert helen["personal_folder"] == "Personal/helen"
