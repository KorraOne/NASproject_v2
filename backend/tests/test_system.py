"""System API tests."""

import os

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def admin_headers(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_system_info(client, admin_headers, setup_complete, tmp_path, monkeypatch):
    monkeypatch.setattr("frogswork_api.services.system.DATA_ROOT", tmp_path)
    response = client.get("/api/system/info", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["hostname"]
    assert body["uptime_seconds"] >= 0
    assert body["version"]


def test_ssh_default_off(client, admin_headers, setup_complete):
    response = client.get("/api/system/ssh", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["remote_enabled"] is False


def test_ssh_toggle(client, admin_headers, setup_complete):
    enabled = client.post(
        "/api/system/ssh",
        headers=admin_headers,
        json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["remote_enabled"] is True

    disabled = client.post(
        "/api/system/ssh",
        headers=admin_headers,
        json={"enabled": False},
    )
    assert disabled.json()["remote_enabled"] is False


def test_reboot_requires_confirm(client, admin_headers, setup_complete):
    response = client.post(
        "/api/system/reboot",
        headers=admin_headers,
        json={"confirm": False},
    )
    assert response.status_code == 400

    ok = client.post(
        "/api/system/reboot",
        headers=admin_headers,
        json={"confirm": True},
    )
    assert ok.status_code == 200
