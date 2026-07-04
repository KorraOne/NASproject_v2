"""Storage overview API tests."""

import os

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_storage_requires_auth(client, setup_complete):
    assert client.get("/api/storage").status_code == 401


def test_storage_overview(client, admin_headers, setup_complete, tmp_path, monkeypatch):
    monkeypatch.setattr("frogswork_api.storage.router.DATA_ROOT", tmp_path)
    response = client.get("/api/storage", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_bytes"] > 0
    assert body["used_bytes"] >= 0
    assert body["free_bytes"] >= 0
    assert body["file_user_count"] == 0
    assert body["shared_folder_count"] == 3
