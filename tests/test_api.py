from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_validate_endpoint():
    response = client.post("/api/validate", json={"markdown": "# Test"})
    assert response.status_code == 200
    assert response.json()["passed"] is False


def test_job_not_found():
    response = client.get("/api/jobs/does-not-exist")
    assert response.status_code == 404
