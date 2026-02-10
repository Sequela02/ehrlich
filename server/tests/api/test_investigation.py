import pytest
from fastapi.testclient import TestClient

from ehrlich.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestStartInvestigation:
    def test_creates_investigation(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/investigate",
            json={"prompt": "Find antimicrobials for MRSA"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_missing_prompt(self, client: TestClient) -> None:
        response = client.post("/api/v1/investigate", json={})
        assert response.status_code == 422


class TestStreamInvestigation:
    def test_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/investigate/nonexistent/stream")
        assert response.status_code == 404

    def test_already_started(self, client: TestClient) -> None:
        # Create investigation
        resp = client.post(
            "/api/v1/investigate",
            json={"prompt": "Test"},
        )
        inv_id = resp.json()["id"]

        # Manually mark as running to simulate already started
        from ehrlich.api.routes.investigation import _investigations
        from ehrlich.investigation.domain.investigation import InvestigationStatus

        _investigations[inv_id].status = InvestigationStatus.RUNNING

        response = client.get(f"/api/v1/investigate/{inv_id}/stream")
        assert response.status_code == 409
