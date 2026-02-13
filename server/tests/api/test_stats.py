import pytest
from fastapi.testclient import TestClient

from ehrlich.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


class TestStats:
    def test_returns_all_fields(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "tool_count" in data
        assert "domain_count" in data
        assert "phase_count" in data
        assert "data_source_count" in data
        assert "event_type_count" in data

    def test_tool_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert data["tool_count"] == 70

    def test_domain_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert data["domain_count"] == 3

    def test_phase_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert data["phase_count"] == 6

    def test_data_source_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert data["data_source_count"] == 16

    def test_event_type_count(self, client: TestClient) -> None:
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert data["event_type_count"] == 20
