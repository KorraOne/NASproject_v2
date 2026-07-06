"""Device identity and claim-code tests."""

import os

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")

from fastapi.testclient import TestClient

from frogswork_api.db import connect, init_db
from frogswork_api.main import app
from frogswork_api.services import device_identity


def test_claim_code_required_when_seeded(tmp_path, monkeypatch):
    db_path = tmp_path / "claim.db"
    data_shared = tmp_path / "frogswork"
    data_shared.mkdir()
    data_personal = data_shared / "Personal"
    data_personal.mkdir()

    monkeypatch.setenv("FROGSWORK_DB_PATH", str(db_path))
    monkeypatch.setenv("FROGSWORK_JWT_SECRET", "test-jwt-secret-key-for-pytest-only")
    monkeypatch.setenv("FROGSWORK_SKIP_SYSTEM", "1")
    monkeypatch.delenv("FROGSWORK_SKIP_CLAIM", raising=False)
    monkeypatch.setattr("frogswork_api.setup.router.DATA_FROGSWORK", data_shared)
    monkeypatch.setattr("frogswork_api.paths.DATA_FROGSWORK", data_shared)

    init_db(db_path)
    with connect(db_path) as conn:
        device_identity.seed_device_identity(
            conn,
            serial="FW-2026-00001",
            claim_code="FW-7K3M-9P2Q",
            software_version="1.0.0",
        )

    with TestClient(app) as client:
        status = client.get("/api/setup/status")
        assert status.json()["requires_claim_code"] is True

        bad = client.post(
            "/api/setup",
            json={
                "password": "test-admin-pass",
                "timezone": "UTC",
                "claim_code": "FW-7K3M-9P9Q",
                "email": "owner@example.com",
            },
        )
        assert bad.status_code == 400

        good = client.post(
            "/api/setup",
            json={
                "password": "test-admin-pass",
                "timezone": "UTC",
                "claim_code": "FW-7K3M-9P2Q",
                "email": "owner@example.com",
            },
        )
        assert good.status_code == 200
        assert good.json()["access_token"]

        login = client.post(
            "/api/auth/login",
            json={"email": "owner@example.com", "password": "test-admin-pass"},
        )
        assert login.status_code == 200


def test_email_login_rejects_wrong_email(client, setup_complete):
    with connect() as conn:
        conn.execute(
            "UPDATE dashboard_admin SET email = ? WHERE id = 1",
            ("owner@example.com",),
        )
    wrong = client.post(
        "/api/auth/login",
        json={"email": "other@example.com", "password": "test-admin-pass"},
    )
    assert wrong.status_code == 401
