"""Storage settings and layout tests."""

import os

import pytest

from frogswork_api.db import connect, get_setting, set_setting
from frogswork_api.services.system import DEFAULT_PERSONAL_QUOTA_KEY

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_reserved_personal_folder_name(client, admin_headers, setup_complete):
    response = client.post(
        "/api/folders",
        headers=admin_headers,
        json={"name": "Personal"},
    )
    assert response.status_code == 400
    assert "reserved" in response.json()["detail"].lower()


def test_default_personal_quota_applied_on_user_create(client, admin_headers, setup_complete, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.users.linux_users.create_linux_user", lambda u: None)
    monkeypatch.setattr("frogswork_api.services.users.linux_users.set_quota", lambda u, q: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.set_password", lambda u, p: None)
    monkeypatch.setattr("frogswork_api.services.users.samba.reload_samba", lambda: None)
    monkeypatch.setattr("frogswork_api.services.users.share_layout.sync_all_layout_acls", lambda c: None)

    with connect() as conn:
        set_setting(conn, DEFAULT_PERSONAL_QUOTA_KEY, str(5 * 1024**3))

    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"username": "carol", "password": "carol-pass-1"},
    )
    assert response.status_code == 201
    assert response.json()["quota_bytes"] == 5 * 1024**3


def test_storage_settings_api(client, admin_headers, setup_complete):
    response = client.patch(
        "/api/system/storage-settings",
        headers=admin_headers,
        json={"default_personal_quota_bytes": 10 * 1024**3},
    )
    assert response.status_code == 200
    assert response.json()["default_personal_quota_bytes"] == 10 * 1024**3

    get_resp = client.get("/api/system/storage-settings", headers=admin_headers)
    assert get_resp.json()["default_personal_quota_bytes"] == 10 * 1024**3

    with connect() as conn:
        assert get_setting(conn, DEFAULT_PERSONAL_QUOTA_KEY) == str(10 * 1024**3)
