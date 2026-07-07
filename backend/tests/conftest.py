"""Shared pytest fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def pytest_configure(config) -> None:
    """Point runtime paths at a writable temp directory before test modules import the app."""
    if os.environ.get("PYTEST_FROGSWORK_CONFIGURED") == "1":
        return

    base = Path(tempfile.mkdtemp(prefix="frogswork-pytest-"))
    state_dir = base / "state"
    data_root = base / "data"
    frogswork_root = data_root / "frogswork"
    personal = frogswork_root / "Personal"
    snapshots = data_root / ".snapshots"
    for path in (state_dir, frogswork_root, personal, snapshots):
        path.mkdir(parents=True, exist_ok=True)

    os.environ["PYTEST_FROGSWORK_CONFIGURED"] = "1"
    os.environ.setdefault("FROGSWORK_STATE_DIR", str(state_dir))
    os.environ.setdefault("FROGSWORK_DATA_ROOT", str(data_root))
    os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")
    os.environ.setdefault("FROGSWORK_SKIP_CLAIM", "1")
    os.environ.setdefault("FROGSWORK_JWT_SECRET", "test-jwt-secret-key-for-pytest-only")


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"

    monkeypatch.setenv("FROGSWORK_DB_PATH", str(db_path))
    monkeypatch.setenv("FROGSWORK_SKIP_SYSTEM", "1")
    monkeypatch.setenv("FROGSWORK_SKIP_CLAIM", "1")

    from frogswork_api.db import init_db
    from frogswork_api.main import app

    init_db(db_path)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def setup_complete(client):
    response = client.post(
        "/api/setup",
        json={"password": "test-admin-pass", "timezone": "UTC"},
    )
    assert response.status_code == 200
    return response
