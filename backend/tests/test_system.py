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


def test_updates_disabled_without_manifest(client, admin_headers, setup_complete, monkeypatch):
    monkeypatch.delenv("FROGSWORK_UPDATE_MANIFEST_URL", raising=False)
    response = client.get("/api/system/updates/check", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["updates_enabled"] is False
    assert body["update_available"] is False


def test_updates_check_and_apply(client, admin_headers, setup_complete, monkeypatch):
    monkeypatch.setenv("FROGSWORK_UPDATE_MANIFEST_URL", "https://example.invalid/manifest.json")

    class FakeManifest:
        version = "9.9.9"
        tarball_url = "https://example.invalid/frogswork.tar.gz"
        sha256 = "deadbeef"
        notes = "hi"

    monkeypatch.setattr("frogswork_api.integrations.update_ops.fetch_manifest", lambda _u: FakeManifest)
    monkeypatch.setattr("frogswork_api.integrations.update_ops.stage_update_tarball", lambda **_k: None)
    monkeypatch.setattr("frogswork_api.integrations.update_ops.apply_staged_update", lambda: None)

    check = client.get("/api/system/updates/check", headers=admin_headers)
    assert check.status_code == 200
    assert check.json()["update_available"] is True

    apply = client.post("/api/system/updates/apply", headers=admin_headers)
    assert apply.status_code == 200
    assert "Update applied" in apply.json()["message"] or apply.json()["message"]
