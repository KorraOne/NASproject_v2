from fastapi.testclient import TestClient

from frogswork_api.main import app
from frogswork_api.paths import read_version

client = TestClient(app)


def test_app_title():
    assert app.title == "FrogsWork File Storage API"


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == read_version()
