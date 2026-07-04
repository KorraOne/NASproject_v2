"""Snapshot API tests."""

import os
from datetime import date

import pytest

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


@pytest.fixture
def snapshot_env(client, setup_complete, tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    snapshots = data_root / ".snapshots"
    shared = data_root / "shared" / "Projects"
    shared.mkdir(parents=True)
    (shared / "report.txt").write_text("original", encoding="utf-8")
    snapshots.mkdir(parents=True)

    monkeypatch.setattr("frogswork_api.integrations.btrfs.DATA_ROOT", data_root)
    monkeypatch.setattr("frogswork_api.integrations.btrfs.DATA_SNAPSHOTS", snapshots)
    monkeypatch.setattr("frogswork_api.paths.DATA_ROOT", data_root)
    monkeypatch.setattr("frogswork_api.paths.DATA_SNAPSHOTS", snapshots)

    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers, data_root, snapshots


def test_list_snapshots_empty(snapshot_env):
    client, headers, _, _ = snapshot_env
    response = client.get("/api/snapshots", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_snapshot(snapshot_env):
    client, headers, _, snapshots = snapshot_env
    created = client.post("/api/snapshots", headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["kind"] == "daily"
    assert (snapshots / body["id"]).is_dir()

    listed = client.get("/api/snapshots", headers=headers).json()
    assert len(listed) == 1


def test_snapshot_settings(snapshot_env):
    client, headers, _, _ = snapshot_env
    settings = client.get("/api/snapshots/settings", headers=headers).json()
    assert settings["snapshot_hour"] == 2
    assert settings["retention_daily"] == 7

    updated = client.patch(
        "/api/snapshots/settings",
        headers=headers,
        json={"retention_daily": 10},
    )
    assert updated.status_code == 200
    assert updated.json()["retention_daily"] == 10


def test_browse_and_restore(snapshot_env, monkeypatch):
    client, headers, data_root, snapshots = snapshot_env
    day = date.today().isoformat()
    snap_id = f"daily-{day}"
    snap_shared = snapshots / snap_id / "shared" / "Projects"
    snap_shared.mkdir(parents=True)
    (snap_shared / "report.txt").write_text("from snapshot", encoding="utf-8")

    live_file = data_root / "shared" / "Projects" / "report.txt"
    live_file.write_text("deleted", encoding="utf-8")

    browse = client.get(f"/api/snapshots/{snap_id}/browse", headers=headers, params={"path": "shared/Projects"})
    assert browse.status_code == 200
    assert any(entry["name"] == "report.txt" for entry in browse.json())

    token_resp = client.get(
        f"/api/snapshots/{snap_id}/restore-token",
        headers=headers,
        params={"path": "shared/Projects/report.txt"},
    )
    token = token_resp.json()["confirm_token"]

    restore = client.post(
        f"/api/snapshots/{snap_id}/restore",
        headers=headers,
        json={"source_path": "shared/Projects/report.txt", "confirm_token": token},
    )
    assert restore.status_code == 200
    assert live_file.read_text(encoding="utf-8") == "from snapshot"
