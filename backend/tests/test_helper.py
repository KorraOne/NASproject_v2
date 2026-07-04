"""Helper API tests."""

import os
from base64 import b64encode

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice_basic(client, setup_complete, admin_headers, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)

    client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "alice", "password": "alice-pass-1"},
    )
    token = b64encode(b"alice:alice-pass-1").decode("ascii")
    return {"Authorization": f"Basic {token}"}


def test_helper_mounts(client, alice_basic, setup_complete):
    response = client.get("/api/helper/mounts", headers=alice_basic)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["mounts"][0]["suggested_letter"] == "U"
    assert body["mounts"][0]["kind"] == "private"


def test_helper_mounts_requires_auth(client, setup_complete):
    assert client.get("/api/helper/mounts").status_code == 401


def test_helper_download_missing(client):
    response = client.get("/api/helper/download")
    assert response.status_code == 404
