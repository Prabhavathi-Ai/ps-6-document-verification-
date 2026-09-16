from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_app_starts() -> None:
    response = client.get("/api/v1")
    assert response.status_code == 200


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "veridoc-api"
    assert "version" in payload
    assert "environment" in payload
