from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.sports.infrastructure.dsld_client import DSLDClient


@pytest.fixture
def client() -> DSLDClient:
    return DSLDClient()


_BASE = "https://api.ods.od.nih.gov/dsld/v9/browse-ingredients"

_DSLD_RESPONSE = {
    "list": [
        {
            "dsld_id": "12345",
            "product_name": "Super Creatine Plus",
            "brand_name": "MuscleTech",
            "serving_size": "1 scoop (5g)",
            "ingredients": [
                {
                    "name": "Creatine Monohydrate",
                    "amount": "5",
                    "unit": "g",
                    "daily_value_pct": None,
                },
                {
                    "name": "Vitamin B12",
                    "amount": "6",
                    "unit": "mcg",
                    "daily_value_pct": 250.0,
                },
            ],
        }
    ]
}


class TestSearchLabels:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_labels(self, client: DSLDClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json=_DSLD_RESPONSE))

        labels = await client.search_labels("creatine")
        assert len(labels) == 1
        lb = labels[0]
        assert lb.report_id == "12345"
        assert lb.product_name == "Super Creatine Plus"
        assert lb.brand == "MuscleTech"
        assert lb.serving_size == "1 scoop (5g)"
        assert len(lb.ingredients) == 2
        assert lb.ingredients[0].name == "Creatine Monohydrate"
        assert lb.ingredients[0].amount == "5"
        assert lb.ingredients[0].unit == "g"
        assert lb.ingredients[1].daily_value_pct == 250.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: DSLDClient) -> None:
        respx.get(_BASE).mock(return_value=Response(200, json={"list": []}))
        labels = await client.search_labels("nonexistent")
        assert labels == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: DSLDClient) -> None:
        respx.get(_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="NIH DSLD"):
            await client.search_labels("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: DSLDClient) -> None:
        route = respx.get(_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json={"list": []}),
        ]
        labels = await client.search_labels("retry test")
        assert labels == []


class TestParseResult:
    def test_missing_dsld_id(self) -> None:
        result = DSLDClient._parse_ingredient_result({})
        assert result is None

    def test_no_ingredients(self) -> None:
        result = DSLDClient._parse_ingredient_result(
            {"dsld_id": "1", "product_name": "Test", "brand_name": "B", "serving_size": "1g"}
        )
        assert result is not None
        assert result.ingredients == ()
