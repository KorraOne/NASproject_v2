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
    monkeypatch.setenv("FROGSWORK_SKIP_SYSTEM", "1")
    monkeypatch.setattr("frogswork_api.setup.router.DATA_SHARED", data_shared)
    monkeypatch.setattr("frogswork_api.services.folders.DATA_SHARED", data_shared)
    monkeypatch.setattr("frogswork_api.paths.DATA_SHARED", data_shared)

    samba_staging = tmp_path / "samba-staging"
    samba_d = tmp_path / "shares.d"
    samba_staging.mkdir()
    samba_d.mkdir()
    monkeypatch.setattr("frogswork_api.integrations.samba_shares.SAMBA_SHARES_STAGING", samba_staging)
    monkeypatch.setattr("frogswork_api.integrations.samba_shares.SAMBA_SHARES_D", samba_d)

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
