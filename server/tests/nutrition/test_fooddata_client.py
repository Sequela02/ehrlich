from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.nutrition.infrastructure.fooddata_client import FoodDataClient


@pytest.fixture
def client() -> FoodDataClient:
    return FoodDataClient(api_key="TEST_KEY")


_BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"

_FOOD_RESPONSE = {
    "foods": [
        {
            "fdcId": 171077,
            "description": "Chicken, breast, skinless, boneless, raw",
            "brandName": "",
            "brandOwner": "",
            "foodCategory": "Poultry Products",
            "foodNutrients": [
                {
                    "nutrientName": "Protein",
                    "value": 23.09,
                    "unitName": "G",
                    "nutrientNumber": "203",
                },
                {
                    "nutrientName": "Total lipid (fat)",
                    "value": 1.24,
                    "unitName": "G",
                    "nutrientNumber": "204",
                },
                {
                    "nutrientName": "Energy",
                    "value": 120,
                    "unitName": "KCAL",
                    "nutrientNumber": "208",
                },
            ],
        }
    ]
}


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_profiles(self, client: FoodDataClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_FOOD_RESPONSE))

        profiles = await client.search("chicken breast")
        assert len(profiles) == 1
        p = profiles[0]
        assert p.fdc_id == 171077
        assert "Chicken" in p.description
        assert p.category == "Poultry Products"
        assert len(p.nutrients) == 3
        assert p.nutrients[0].name == "Protein"
        assert p.nutrients[0].amount == 23.09
        assert p.nutrients[0].unit == "G"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: FoodDataClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"foods": []}))
        profiles = await client.search("nonexistent food")
        assert profiles == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: FoodDataClient) -> None:
        respx.get(_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="USDA FoodData"):
            await client.search("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: FoodDataClient) -> None:
        route = respx.get(_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json={"foods": []}),
        ]
        profiles = await client.search("retry test")
        assert profiles == []


class TestParseFood:
    def test_missing_fields(self) -> None:
        profile = FoodDataClient._parse_food({})
        assert profile.fdc_id == 0
        assert profile.description == ""
        assert profile.nutrients == ()
