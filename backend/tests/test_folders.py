"""Shared folder and permission API tests."""

import os

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice_and_bob(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)

    alice = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "alice", "password": "alice-pass-1"},
    ).json()
    bob = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "bob", "password": "bob-pass-1"},
    ).json()
    return alice, bob


def test_list_seeded_folders(client, admin_headers, setup_complete):
    response = client.get("/api/folders", headers=admin_headers)
    assert response.status_code == 200
    names = {f["name"] for f in response.json()}
    assert names == {"Projects", "Invoices", "Shared"}
    projects = next(f for f in response.json() if f["name"] == "Projects")
    assert projects["share_name"] == "shared-Projects"
    assert projects["permissions"] == []


def test_create_folder(client, admin_headers, setup_complete):
    response = client.post(
        "/api/folders",
        headers=admin_headers,
        json={"name": "Marketing"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Marketing"
    assert body["share_name"] == "shared-Marketing"
    assert body["permissions"] == []


def test_replace_folder_permissions(client, admin_headers, alice_and_bob, setup_complete):
    alice, bob = alice_and_bob
    folders = client.get("/api/folders", headers=admin_headers).json()
    projects_id = next(f["id"] for f in folders if f["name"] == "Projects")

    response = client.put(
        f"/api/folders/{projects_id}/permissions",
        headers=admin_headers,
        json={
            "permissions": [
                {"user_id": alice["id"], "access": "read"},
                {"user_id": bob["id"], "access": "read_write"},
            ]
        },
    )
    assert response.status_code == 200
    perms = {p["username"]: p["access"] for p in response.json()}
    assert perms == {"alice": "read", "bob": "read_write"}


def test_user_patch_folder_permissions(client, admin_headers, alice_and_bob, setup_complete):
    alice, _bob = alice_and_bob
    folders = client.get("/api/folders", headers=admin_headers).json()
    invoices_id = next(f["id"] for f in folders if f["name"] == "Invoices")

    response = client.patch(
        f"/api/users/{alice['id']}",
        headers=admin_headers,
        json={"folder_permissions": [{"folder_id": invoices_id, "access": "read_write"}]},
    )
    assert response.status_code == 200

    folder = client.get(f"/api/folders/{invoices_id}", headers=admin_headers).json()
    assert len(folder["permissions"]) == 1
    assert folder["permissions"][0]["username"] == "alice"
    assert folder["permissions"][0]["access"] == "read_write"


def test_delete_empty_folder(client, admin_headers, setup_complete):
    created = client.post(
        "/api/folders",
        headers=admin_headers,
        json={"name": "Temp"},
    ).json()
    response = client.delete(f"/api/folders/{created['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert client.get(f"/api/folders/{created['id']}", headers=admin_headers).status_code == 404
