def test_login_before_setup(client):
    response = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    assert response.status_code == 503


def test_login_success(client, setup_complete):
    response = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password(client, setup_complete):
    response = client.post("/api/auth/login", json={"password": "wrong-password"})
    assert response.status_code == 401


def test_me_requires_auth(client, setup_complete):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_token(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "dashboard_admin"


def test_logout(client, setup_complete):
    login = client.post("/api/auth/login", json={"password": "test-admin-pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Signed out."
