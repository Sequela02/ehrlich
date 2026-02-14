import os

import httpx
import pytest

from ehrlich.api.app import create_app
from ehrlich.api.auth import get_current_user, get_current_user_sse
from ehrlich.api.routes import investigation as inv_module
from ehrlich.investigation.domain.investigation import InvestigationStatus

_TEST_DATABASE_URL = os.environ.get(
    "EHRLICH_TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ehrlich_test",
)

_TEST_USER = {"workos_id": "workos_inv_test", "email": "inv@test.com"}
_OTHER_USER = {"workos_id": "workos_other_user", "email": "other@test.com"}


async def _mock_user() -> dict[str, str]:
    return _TEST_USER


async def _mock_other_user() -> dict[str, str]:
    return _OTHER_USER


@pytest.fixture
async def client() -> httpx.AsyncClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_current_user_sse] = _mock_user

    await inv_module.init_repository(_TEST_DATABASE_URL)
    repo = inv_module._get_repository()
    pool = repo._get_pool()
    async with pool.acquire() as c:
        await c.execute("DELETE FROM events")
        await c.execute("DELETE FROM credit_transactions")
        await c.execute("DELETE FROM investigations")
        await c.execute("DELETE FROM users")
    await repo.get_or_create_user(_TEST_USER["workos_id"], _TEST_USER["email"])
    await repo.get_or_create_user(_OTHER_USER["workos_id"], _OTHER_USER["email"])

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]

    await inv_module.close_repository()


class TestStartInvestigation:
    async def test_creates_investigation(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Find antimicrobials for MRSA", "director_tier": "haiku"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    async def test_missing_prompt(self, client: httpx.AsyncClient) -> None:
        response = await client.post("/api/v1/investigate", json={})
        assert response.status_code == 422


class TestListInvestigations:
    async def test_empty_list(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v1/investigate")
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_created_investigations(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test 1", "director_tier": "haiku"},
        )
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test 2", "director_tier": "haiku"},
        )

        response = await client.get("/api/v1/investigate")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["prompt"] == "Test 2"
        assert data[1]["prompt"] == "Test 1"


class TestGetInvestigation:
    async def test_returns_investigation(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test", "director_tier": "haiku"},
        )
        inv_id = resp.json()["id"]

        response = await client.get(f"/api/v1/investigate/{inv_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == inv_id
        assert data["prompt"] == "Test"
        assert data["status"] == "pending"

    async def test_not_found(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v1/investigate/nonexistent")
        assert response.status_code == 404


class TestStreamInvestigation:
    async def test_not_found(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v1/investigate/nonexistent/stream")
        assert response.status_code == 404

    async def test_completed_replays_final(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test", "director_tier": "haiku"},
        )
        inv_id = resp.json()["id"]

        repo = inv_module._get_repository()
        inv = await repo.get_by_id(inv_id)
        assert inv is not None
        inv.status = InvestigationStatus.COMPLETED
        inv.summary = "Found 2 candidates"
        await repo.update(inv)

        response = await client.get(f"/api/v1/investigate/{inv_id}/stream")
        assert response.status_code == 200


class TestOwnership:
    async def test_get_investigation_forbidden_for_other_user(
        self, client: httpx.AsyncClient
    ) -> None:
        # Create investigation as TEST_USER
        resp = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test", "director_tier": "haiku"},
        )
        inv_id = resp.json()["id"]

        # Switch to OTHER_USER
        app = client._transport.app  # type: ignore[union-attr]
        app.dependency_overrides[get_current_user] = _mock_other_user
        app.dependency_overrides[get_current_user_sse] = _mock_other_user

        response = await client.get(f"/api/v1/investigate/{inv_id}")
        assert response.status_code == 403

    async def test_stream_forbidden_for_other_user(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test", "director_tier": "haiku"},
        )
        inv_id = resp.json()["id"]

        # Mark completed so stream replays (avoids starting orchestrator)
        repo = inv_module._get_repository()
        inv = await repo.get_by_id(inv_id)
        assert inv is not None
        inv.status = InvestigationStatus.COMPLETED
        inv.summary = "Done"
        await repo.update(inv)

        # Switch user
        app = client._transport.app  # type: ignore[union-attr]
        app.dependency_overrides[get_current_user] = _mock_other_user
        app.dependency_overrides[get_current_user_sse] = _mock_other_user

        response = await client.get(f"/api/v1/investigate/{inv_id}/stream")
        assert response.status_code == 403

    async def test_list_only_own_investigations(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "User 1 investigation", "director_tier": "haiku"},
        )

        # Switch user
        app = client._transport.app  # type: ignore[union-attr]
        app.dependency_overrides[get_current_user] = _mock_other_user

        response = await client.get("/api/v1/investigate")
        assert response.status_code == 200
        assert response.json() == []
