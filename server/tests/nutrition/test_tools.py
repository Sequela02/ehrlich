"""Tests for Nutrition Science tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.literature.domain.paper import Paper
from ehrlich.nutrition.domain.entities import (
    AdverseEvent,
    IngredientEntry,
    NutrientEntry,
    NutrientProfile,
    SupplementLabel,
)
from ehrlich.nutrition.tools import (
    search_nutrient_data,
    search_supplement_evidence,
    search_supplement_labels,
    search_supplement_safety,
)


@pytest.fixture()
def mock_scholar():
    papers = [
        Paper(
            title="HIIT vs MICT for VO2max",
            authors=["Smith J"],
            year=2023,
            doi="10.1234/test",
            abstract="This study compared HIIT and MICT protocols.",
            citations=42,
            source="semantic_scholar",
        ),
    ]
    with patch(
        "ehrlich.nutrition.tools._client.search",
        new_callable=AsyncMock,
        return_value=papers,
    ) as mock:
        yield mock


class TestSearchSupplementEvidence:
    @pytest.mark.asyncio()
    async def test_returns_papers(self, mock_scholar: AsyncMock) -> None:
        result = json.loads(
            await search_supplement_evidence("creatine", "strength")
        )
        assert result["supplement"] == "creatine"
        assert result["outcome"] == "strength"
        assert result["count"] == 1


class TestSearchSupplementLabels:
    @pytest.mark.asyncio()
    async def test_returns_labels(self) -> None:
        labels = [
            SupplementLabel(
                report_id="123",
                product_name="Creatine Plus",
                brand="Brand",
                ingredients=(
                    IngredientEntry(name="Creatine", amount="5", unit="g"),
                ),
                serving_size="1 scoop",
            )
        ]
        with patch(
            "ehrlich.nutrition.tools._service.search_supplement_labels",
            new_callable=AsyncMock,
            return_value=labels,
        ):
            result = json.loads(await search_supplement_labels("creatine"))
            assert result["count"] == 1
            assert result["products"][0]["product_name"] == "Creatine Plus"
            assert len(result["products"][0]["ingredients"]) == 1


class TestSearchNutrientData:
    @pytest.mark.asyncio()
    async def test_returns_profiles(self) -> None:
        profiles = [
            NutrientProfile(
                fdc_id=171077,
                description="Chicken breast",
                brand="",
                category="Poultry",
                nutrients=(
                    NutrientEntry(name="Protein", amount=23.0, unit="G", nutrient_number="203"),
                ),
            )
        ]
        with patch(
            "ehrlich.nutrition.tools._service.search_nutrient_data",
            new_callable=AsyncMock,
            return_value=profiles,
        ):
            result = json.loads(await search_nutrient_data("chicken breast"))
            assert result["count"] == 1
            assert result["foods"][0]["fdc_id"] == 171077
            assert result["foods"][0]["nutrients"][0]["name"] == "Protein"


class TestSearchSupplementSafety:
    @pytest.mark.asyncio()
    async def test_returns_events(self) -> None:
        events = [
            AdverseEvent(
                report_id="FDA-001",
                date="20230315",
                products=("Pre-Workout X",),
                reactions=("NAUSEA",),
                outcomes=("Hospitalization",),
                consumer_age="28",
                consumer_gender="Male",
            )
        ]
        with patch(
            "ehrlich.nutrition.tools._service.search_supplement_safety",
            new_callable=AsyncMock,
            return_value=events,
        ):
            result = json.loads(await search_supplement_safety("pre-workout"))
            assert result["count"] == 1
            assert result["adverse_events"][0]["report_id"] == "FDA-001"
            assert "NAUSEA" in result["adverse_events"][0]["reactions"]
