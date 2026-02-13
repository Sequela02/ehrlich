from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.training.infrastructure.wger_client import WgerClient

_BASE_URL = "https://wger.de/api/v2/exercise/"


@pytest.fixture()
def client() -> WgerClient:
    return WgerClient()


_EXERCISE_RESPONSE = {
    "results": [
        {
            "id": 1,
            "name": "Bench Press",
            "category": {"name": "Chest"},
            "muscles": [{"name": "Pectoralis major"}],
            "muscles_secondary": [{"name": "Triceps"}],
            "equipment": [{"name": "Barbell"}],
            "description": "<p>Lie on bench and press.</p>",
        }
    ]
}


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_exercises(self, client: WgerClient) -> None:
        respx.get(_BASE_URL).mock(return_value=Response(200, json=_EXERCISE_RESPONSE))

        exercises = await client.search()
        assert len(exercises) == 1
        e = exercises[0]
        assert e.id == 1
        assert e.name == "Bench Press"
        assert e.category == "Chest"
        assert e.muscles_primary == ("Pectoralis major",)
        assert e.muscles_secondary == ("Triceps",)
        assert e.equipment == ("Barbell",)
        assert e.description == "Lie on bench and press."
        assert "<p>" not in e.description

    @respx.mock
    @pytest.mark.asyncio()
    async def test_empty_results(self, client: WgerClient) -> None:
        respx.get(_BASE_URL).mock(return_value=Response(200, json={"results": []}))
        exercises = await client.search()
        assert exercises == []

    @respx.mock
    @pytest.mark.asyncio()
    async def test_filter_by_muscle(self, client: WgerClient) -> None:
        route = respx.get(_BASE_URL).mock(return_value=Response(200, json={"results": []}))
        await client.search(muscle_group="chest")
        request = route.calls[0].request
        assert request.url.params.get("muscles") == "4"

    @respx.mock
    @pytest.mark.asyncio()
    async def test_http_error(self, client: WgerClient) -> None:
        respx.get(_BASE_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="wger"):
            await client.search()
