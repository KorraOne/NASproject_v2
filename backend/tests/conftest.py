"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frogswork_api.db import init_db
from frogswork_api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    data_shared = tmp_path / "shared"
    data_shared.mkdir()

    monkeypatch.setenv("FROGSWORK_DB_PATH", str(db_path))
    monkeypatch.setenv("FROGSWORK_JWT_SECRET", "test-jwt-secret-key-for-pytest-only")
    monkeypatch.setattr("frogswork_api.setup.router.DATA_SHARED", data_shared)

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
