def test_setup_status_before_setup(client):
    response = client.get("/api/setup/status")
    assert response.status_code == 200
    assert response.json() == {"setup_complete": False}


def test_complete_setup(client):
    response = client.post(
        "/api/setup",
        json={"password": "test-admin-pass", "timezone": "Australia/Sydney"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["setup_complete"] is True

    status = client.get("/api/setup/status")
    assert status.json()["setup_complete"] is True


def test_setup_rejects_duplicate(client, setup_complete):
    response = client.post(
        "/api/setup",
        json={"password": "another-pass", "timezone": "UTC"},
    )
    assert response.status_code == 409


def test_setup_rejects_short_password(client):
    response = client.post(
        "/api/setup",
        json={"password": "short", "timezone": "UTC"},
    )
    assert response.status_code == 422
