"""File user API tests with system integrations skipped."""

import os

import pytest

# Skip real useradd/smbpasswd during tests
os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_users_empty(client, admin_headers):
    response = client.get("/api/users", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_user(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)

    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "alice",
            "display_name": "Alice",
            "password": "alice-pass-1",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["display_name"] == "Alice"
    assert body["archetype_name"] == "Standard Employee"
    assert body["is_superuser"] is False


def test_create_user_requires_auth(client, setup_complete):
    response = client.post(
        "/api/users",
        json={"username": "bob", "password": "bob-pass-1"},
    )
    assert response.status_code == 401


def test_create_duplicate_user(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)

    payload = {"username": "carol", "password": "carol-pass-1"}
    assert client.post("/api/users", headers=admin_headers, json=payload).status_code == 201
    assert client.post("/api/users", headers=admin_headers, json=payload).status_code == 409


def test_delete_user(client, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.delete_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.linux_users.delete_linux_user", lambda u: None)

    created = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "dave", "password": "dave-pass-1"},
    ).json()
    user_id = created["id"]

    response = client.delete(f"/api/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    assert client.get(f"/api/users/{user_id}", headers=admin_headers).status_code == 404
