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


def test_vault_folders_endpoint(monkeypatch):
    monkeypatch.setattr("app.get_vault_folders", lambda: {"folders": ["AI Agents", "Inbox"], "default": "Inbox"})

    response = client.get("/api/vault/folders")

    assert response.status_code == 200
    assert response.json()["folders"] == ["AI Agents", "Inbox"]
