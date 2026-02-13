"""Tests for credit system and BYOK routes."""

from __future__ import annotations

import os

import httpx
import pytest

from ehrlich.api.app import create_app
from ehrlich.api.auth import get_current_user, get_current_user_sse
from ehrlich.api.routes import investigation as inv_module

_TEST_DATABASE_URL = os.environ.get(
    "EHRLICH_TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ehrlich_test",
)

_TEST_USER = {"workos_id": "workos_credit_test", "email": "credit@test.com"}


async def _mock_user() -> dict[str, str]:
    return _TEST_USER


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

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]

    await inv_module.close_repository()


class TestCreditBalance:
    async def test_returns_default_credits(self, client: httpx.AsyncClient) -> None:
        response = await client.get("/api/v1/credits/balance")
        assert response.status_code == 200
        data = response.json()
        assert data["credits"] == 5
        assert data["is_byok"] is False

    async def test_detects_byok_header(self, client: httpx.AsyncClient) -> None:
        response = await client.get(
            "/api/v1/credits/balance",
            headers={"X-Anthropic-Key": "sk-ant-test123"},
        )
        assert response.status_code == 200
        assert response.json()["is_byok"] is True


class TestStartInvestigationCredits:
    async def test_deducts_credits_on_start(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Test deduction", "director_tier": "haiku"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 4

    async def test_insufficient_credits_returns_402(
        self, client: httpx.AsyncClient
    ) -> None:
        resp1 = await client.post(
            "/api/v1/investigate",
            json={"prompt": "First opus", "director_tier": "opus"},
        )
        assert resp1.status_code == 200

        resp2 = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Second opus", "director_tier": "opus"},
        )
        assert resp2.status_code == 402
        assert "Insufficient credits" in resp2.json()["detail"]

    async def test_byok_skips_credit_check(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/investigate",
            json={"prompt": "BYOK test", "director_tier": "opus"},
            headers={"X-Anthropic-Key": "sk-ant-byok"},
        )
        assert response.status_code == 200

        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 5

    async def test_invalid_tier_returns_400(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/investigate",
            json={"prompt": "Bad tier", "director_tier": "gpt4"},
        )
        assert response.status_code == 400
        assert "Invalid director tier" in response.json()["detail"]


class TestTierCredits:
    async def test_haiku_costs_1(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Haiku test", "director_tier": "haiku"},
        )
        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 4

    async def test_sonnet_costs_3(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Sonnet test", "director_tier": "sonnet"},
        )
        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 2

    async def test_opus_costs_5(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Opus test", "director_tier": "opus"},
        )
        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 0

    async def test_default_tier_is_opus(self, client: httpx.AsyncClient) -> None:
        await client.post(
            "/api/v1/investigate",
            json={"prompt": "Default tier"},
        )
        balance = await client.get("/api/v1/credits/balance")
        assert balance.json()["credits"] == 0
