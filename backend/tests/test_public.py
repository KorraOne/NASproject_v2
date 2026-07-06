"""Public API tests."""

import os

os.environ.setdefault("FROGSWORK_SKIP_SYSTEM", "1")


def test_public_info(client, setup_complete):
    response = client.get("/api/public/info")
    assert response.status_code == 200
    body = response.json()
    assert "hostname" in body
    assert body["help_path"] == "/help"
