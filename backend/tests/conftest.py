"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frogswork_api.db import init_db
from frogswork_api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    data_shared = tmp_path / "frogswork"
    data_shared.mkdir()
    data_personal = data_shared / "Personal"
    data_personal.mkdir()
    frogswork_shared = data_shared

    monkeypatch.setenv("FROGSWORK_DB_PATH", str(db_path))
    monkeypatch.setenv("FROGSWORK_JWT_SECRET", "test-jwt-secret-key-for-pytest-only")
    monkeypatch.setenv("FROGSWORK_SKIP_SYSTEM", "1")
    monkeypatch.setenv("FROGSWORK_SKIP_CLAIM", "1")
    monkeypatch.setattr("frogswork_api.setup.router.DATA_FROGSWORK", frogswork_shared)
    monkeypatch.setattr("frogswork_api.services.folders.DATA_FROGSWORK", frogswork_shared)
    monkeypatch.setattr("frogswork_api.services.folders.DATA_SHARED", frogswork_shared)
    monkeypatch.setattr("frogswork_api.paths.DATA_FROGSWORK", frogswork_shared)
    monkeypatch.setattr("frogswork_api.paths.DATA_SHARED", frogswork_shared)
    monkeypatch.setattr("frogswork_api.paths.DATA_PERSONAL", data_personal)
    monkeypatch.setattr("frogswork_api.paths.DATA_USERS", data_personal)

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
