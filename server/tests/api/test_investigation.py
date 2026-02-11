import pytest
from fastapi.testclient import TestClient

from ehrlich.api.app import create_app
from ehrlich.api.routes import investigation as inv_module


@pytest.fixture
def client(tmp_path) -> TestClient:
    app = create_app()

    # Override the repository with a temp path for tests
    import asyncio

    async def _init() -> None:
        db_path = str(tmp_path / "test.db")
        await inv_module.init_repository(db_path)

    asyncio.get_event_loop().run_until_complete(_init())

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


class TestListInvestigations:
    def test_empty_list(self, client: TestClient) -> None:
        response = client.get("/api/v1/investigate")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_investigations(self, client: TestClient) -> None:
        client.post("/api/v1/investigate", json={"prompt": "Test 1"})
        client.post("/api/v1/investigate", json={"prompt": "Test 2"})

        response = client.get("/api/v1/investigate")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["prompt"] == "Test 2"
        assert data[1]["prompt"] == "Test 1"


class TestGetInvestigation:
    def test_returns_investigation(self, client: TestClient) -> None:
        resp = client.post("/api/v1/investigate", json={"prompt": "Test"})
        inv_id = resp.json()["id"]

        response = client.get(f"/api/v1/investigate/{inv_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inv_id
        assert data["prompt"] == "Test"
        assert data["status"] == "pending"

    def test_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/investigate/nonexistent")
        assert response.status_code == 404


class TestStreamInvestigation:
    def test_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/investigate/nonexistent/stream")
        assert response.status_code == 404

    def test_completed_replays_final(self, client: TestClient) -> None:
        import asyncio

        from ehrlich.investigation.domain.investigation import InvestigationStatus

        resp = client.post("/api/v1/investigate", json={"prompt": "Test"})
        inv_id = resp.json()["id"]

        repo = inv_module._get_repository()

        async def _update() -> None:
            inv = await repo.get_by_id(inv_id)
            assert inv is not None
            inv.status = InvestigationStatus.COMPLETED
            inv.summary = "Found 2 candidates"
            await repo.update(inv)

        asyncio.get_event_loop().run_until_complete(_update())

        response = client.get(f"/api/v1/investigate/{inv_id}/stream")
        assert response.status_code == 200
