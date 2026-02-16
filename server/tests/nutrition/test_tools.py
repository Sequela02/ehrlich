"""Tests for Nutrition Science tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.literature.domain.paper import Paper
from ehrlich.nutrition.domain.entities import (
    AdequacyResult,
    AdverseEvent,
    DrugInteraction,
    IngredientEntry,
    NutrientEntry,
    NutrientProfile,
    NutrientRatio,
    SupplementLabel,
)
from ehrlich.nutrition.tools import (
    analyze_nutrient_ratios,
    assess_nutrient_adequacy,
    check_intake_safety,
    check_interactions,
    compare_nutrients,
    compute_inflammatory_index,
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


_SAMPLE_PROFILE = NutrientProfile(
    fdc_id=171077,
    description="Chicken breast",
    brand="",
    category="Poultry",
    nutrients=(
        NutrientEntry(name="Protein", amount=23.0, unit="G", nutrient_number="203"),
        NutrientEntry(name="Calcium, Ca", amount=800.0, unit="MG", nutrient_number="301"),
        NutrientEntry(name="Iron, Fe", amount=10.0, unit="MG", nutrient_number="303"),
        NutrientEntry(name="Magnesium, Mg", amount=400.0, unit="MG", nutrient_number="304"),
        NutrientEntry(name="Zinc, Zn", amount=11.0, unit="MG", nutrient_number="309"),
        NutrientEntry(name="Copper, Cu", amount=0.9, unit="MG", nutrient_number="312"),
        NutrientEntry(name="Sodium, Na", amount=500.0, unit="MG", nutrient_number="307"),
        NutrientEntry(name="Potassium, K", amount=1000.0, unit="MG", nutrient_number="306"),
        NutrientEntry(name="Phosphorus, P", amount=700.0, unit="MG", nutrient_number="305"),
        NutrientEntry(
            name="Vitamin C, total ascorbic acid", amount=90.0, unit="MG", nutrient_number="401"
        ),
        NutrientEntry(name="Fiber, total dietary", amount=30.0, unit="G", nutrient_number="291"),
        NutrientEntry(
            name="Fatty acids, total saturated", amount=5.0, unit="G", nutrient_number="606"
        ),
        NutrientEntry(name="Cholesterol", amount=80.0, unit="MG", nutrient_number="601"),
        NutrientEntry(name="Vitamin A, RAE", amount=900.0, unit="UG", nutrient_number="320"),
        NutrientEntry(name="Vitamin D (D2 + D3)", amount=15.0, unit="UG", nutrient_number="328"),
        NutrientEntry(
            name="Vitamin E (alpha-tocopherol)", amount=15.0, unit="MG", nutrient_number="323"
        ),
        NutrientEntry(name="Selenium, Se", amount=55.0, unit="UG", nutrient_number="317"),
        NutrientEntry(name="Folate, total", amount=400.0, unit="UG", nutrient_number="417"),
    ),
)


class TestSearchSupplementEvidence:
    @pytest.mark.asyncio()
    async def test_returns_papers(self, mock_scholar: AsyncMock) -> None:
        result = json.loads(await search_supplement_evidence("creatine", "strength"))
        assert result["supplement"] == "creatine"
        assert result["outcome"] == "strength"
        assert result["count"] == 1

    @pytest.mark.asyncio()
    async def test_filters_retracted_papers(self) -> None:
        """Test that retracted papers are filtered out."""
        papers = [
            Paper(
                title="[RETRACTED] Creatine meta-analysis",
                authors=["Bad A"],
                year=2020,
                abstract="Retracted due to fraud.",
            ),
            Paper(
                title="Creatine systematic review",
                authors=["Good B"],
                year=2023,
                abstract="Valid systematic review.",
            ),
            Paper(
                title="Retracted: Creatine RCT",
                authors=["Bad C"],
                year=2022,
                abstract="Retracted paper.",
            ),
        ]
        with patch(
            "ehrlich.nutrition.tools._client.search",
            new_callable=AsyncMock,
            return_value=papers,
        ):
            result = json.loads(await search_supplement_evidence("creatine"))
            assert result["count"] == 1
            assert result["papers"][0]["title"] == "Creatine systematic review"

    @pytest.mark.asyncio()
    async def test_study_type_ranking(self) -> None:
        """Test that meta-analyses rank above systematic reviews, which rank above RCTs."""
        papers = [
            Paper(
                title="Observational study of creatine",
                authors=["Jones C"],
                year=2024,
                abstract="Cohort analysis of creatine use.",
            ),
            Paper(
                title="Creatine meta-analysis",
                authors=["Smith A"],
                year=2022,
                abstract="Meta-analysis of creatine trials.",
            ),
            Paper(
                title="Systematic review of creatine",
                authors=["Brown B"],
                year=2023,
                abstract="Systematic review of creatine effects.",
            ),
            Paper(
                title="RCT on creatine",
                authors=["White D"],
                year=2024,
                abstract="Randomized controlled trial of creatine.",
            ),
        ]
        with patch(
            "ehrlich.nutrition.tools._client.search",
            new_callable=AsyncMock,
            return_value=papers,
        ):
            result = json.loads(await search_supplement_evidence("creatine"))
            assert result["count"] == 4
            # Should be ordered: meta-analysis, systematic review, RCT, observational
            assert "meta-analysis" in result["papers"][0]["title"].lower()
            assert "systematic review" in result["papers"][1]["title"].lower()
            assert "rct" in result["papers"][2]["title"].lower()
            assert "observational" in result["papers"][3]["title"].lower()

    @pytest.mark.asyncio()
    async def test_date_recency_within_same_study_type(self) -> None:
        """Test that more recent papers rank higher within the same study type."""
        papers = [
            Paper(
                title="Creatine RCT 2020",
                authors=["Old A"],
                year=2020,
                abstract="Randomized trial from 2020.",
            ),
            Paper(
                title="Creatine RCT 2024",
                authors=["New B"],
                year=2024,
                abstract="Randomized trial from 2024.",
            ),
        ]
        with patch(
            "ehrlich.nutrition.tools._client.search",
            new_callable=AsyncMock,
            return_value=papers,
        ):
            result = json.loads(await search_supplement_evidence("creatine"))
            assert result["count"] == 2
            # More recent should come first
            assert result["papers"][0]["year"] == 2024
            assert result["papers"][1]["year"] == 2020


class TestSearchSupplementLabels:
    @pytest.mark.asyncio()
    async def test_returns_labels(self) -> None:
        labels = [
            SupplementLabel(
                report_id="123",
                product_name="Creatine Plus",
                brand="Brand",
                ingredients=(IngredientEntry(name="Creatine", amount="5", unit="g"),),
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


class TestCompareNutrients:
    @pytest.mark.asyncio()
    async def test_returns_comparison(self) -> None:
        profiles = [_SAMPLE_PROFILE]
        with patch(
            "ehrlich.nutrition.tools._service.compare_nutrients",
            new_callable=AsyncMock,
            return_value=profiles,
        ):
            result = json.loads(await compare_nutrients("chicken breast, salmon"))
            assert result["count"] == 1
            assert result["queries"] == ["chicken breast", "salmon"]
            assert result["foods"][0]["description"] == "Chicken breast"
            # With only 1 food, no comparison is possible
            assert result["comparison"] == {}
            assert "mar_scores" in result

    @pytest.mark.asyncio()
    async def test_empty_query(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.compare_nutrients",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await compare_nutrients(""))
            assert result["count"] == 0
            assert result["comparison"] == {}
            assert result["mar_scores"] == {}

    @pytest.mark.asyncio()
    async def test_per_nutrient_comparison_and_winner(self) -> None:
        """Test that per-nutrient deltas and winner are computed correctly."""
        profile_a = NutrientProfile(
            fdc_id=1,
            description="Food A",
            brand="",
            category="Test",
            nutrients=(
                NutrientEntry(name="Protein", amount=20.0, unit="G", nutrient_number="203"),
                NutrientEntry(name="Calcium, Ca", amount=100.0, unit="MG", nutrient_number="301"),
            ),
        )
        profile_b = NutrientProfile(
            fdc_id=2,
            description="Food B",
            brand="",
            category="Test",
            nutrients=(
                NutrientEntry(name="Protein", amount=30.0, unit="G", nutrient_number="203"),
                NutrientEntry(name="Calcium, Ca", amount=80.0, unit="MG", nutrient_number="301"),
            ),
        )
        with patch(
            "ehrlich.nutrition.tools._service.compare_nutrients",
            new_callable=AsyncMock,
            return_value=[profile_a, profile_b],
        ):
            result = json.loads(await compare_nutrients("food a, food b"))
            assert result["count"] == 2
            comparison = result["comparison"]
            assert "Protein" in comparison
            assert comparison["Protein"]["winner"] == "Food B"
            assert comparison["Protein"]["amounts"]["Food A"] == 20.0
            assert comparison["Protein"]["amounts"]["Food B"] == 30.0
            assert "Calcium, Ca" in comparison
            assert comparison["Calcium, Ca"]["winner"] == "Food A"

    @pytest.mark.asyncio()
    async def test_mar_score_computation(self) -> None:
        """Test that MAR scores are computed correctly."""
        with patch(
            "ehrlich.nutrition.tools._service.compare_nutrients",
            new_callable=AsyncMock,
            return_value=[_SAMPLE_PROFILE],
        ):
            result = json.loads(await compare_nutrients("chicken breast"))
            assert "mar_scores" in result
            assert "Chicken breast" in result["mar_scores"]
            # MAR score should be a percentage
            assert isinstance(result["mar_scores"]["Chicken breast"], (int, float))


class TestAssessNutrientAdequacy:
    @pytest.mark.asyncio()
    async def test_returns_assessments(self) -> None:
        assessments = [
            AdequacyResult(
                nutrient="Calcium, Ca",
                intake=800.0,
                unit="MG",
                rda=1000.0,
                ear=800.0,
                ul=2500.0,
                pct_rda=80.0,
                status="marginal",
            )
        ]
        with (
            patch(
                "ehrlich.nutrition.tools._service.search_nutrient_data",
                new_callable=AsyncMock,
                return_value=[_SAMPLE_PROFILE],
            ),
            patch(
                "ehrlich.nutrition.tools._service.assess_nutrient_adequacy",
                return_value=assessments,
            ),
        ):
            result = json.loads(await assess_nutrient_adequacy("chicken breast"))
            assert result["count"] == 1
            assert result["food"] == "Chicken breast"
            assert result["assessments"][0]["nutrient"] == "Calcium, Ca"
            assert result["assessments"][0]["status"] == "marginal"

    @pytest.mark.asyncio()
    async def test_no_food_found(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.search_nutrient_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await assess_nutrient_adequacy("nonexistent"))
            assert result["count"] == 0
            assert result["assessments"] == []


class TestCheckIntakeSafety:
    @pytest.mark.asyncio()
    async def test_returns_warnings(self) -> None:
        warnings = [
            AdequacyResult(
                nutrient="Iron, Fe",
                intake=50.0,
                unit="MG",
                rda=8.0,
                ear=6.0,
                ul=45.0,
                pct_rda=625.0,
                status="exceeds_ul",
            )
        ]
        with (
            patch(
                "ehrlich.nutrition.tools._service.search_nutrient_data",
                new_callable=AsyncMock,
                return_value=[_SAMPLE_PROFILE],
            ),
            patch(
                "ehrlich.nutrition.tools._service.check_intake_safety",
                return_value=warnings,
            ),
        ):
            result = json.loads(await check_intake_safety("beef liver"))
            assert result["count"] == 1
            assert result["warnings"][0]["status"] == "exceeds_ul"

    @pytest.mark.asyncio()
    async def test_no_food_found(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.search_nutrient_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await check_intake_safety("nonexistent"))
            assert result["count"] == 0
            assert result["warnings"] == []


class TestCheckInteractions:
    @pytest.mark.asyncio()
    async def test_returns_interactions(self) -> None:
        interactions = [
            DrugInteraction(
                drug_a="warfarin",
                drug_b="aspirin",
                severity="high",
                description="Increased bleeding risk",
                source="RxNav",
            )
        ]
        with patch(
            "ehrlich.nutrition.tools._service.check_interactions",
            new_callable=AsyncMock,
            return_value=interactions,
        ):
            result = json.loads(await check_interactions("warfarin"))
            assert result["count"] == 1
            assert result["substance"] == "warfarin"
            assert result["interactions"][0]["severity"] == "high"

    @pytest.mark.asyncio()
    async def test_no_interactions(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.check_interactions",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await check_interactions("water"))
            assert result["count"] == 0


class TestAnalyzeNutrientRatios:
    @pytest.mark.asyncio()
    async def test_returns_ratios(self) -> None:
        ratios = [
            NutrientRatio(
                name="calcium_to_magnesium",
                value=2.0,
                optimal_min=1.5,
                optimal_max=2.5,
                status="optimal",
            )
        ]
        with (
            patch(
                "ehrlich.nutrition.tools._service.search_nutrient_data",
                new_callable=AsyncMock,
                return_value=[_SAMPLE_PROFILE],
            ),
            patch(
                "ehrlich.nutrition.tools._service.analyze_nutrient_ratios",
                return_value=ratios,
            ),
        ):
            result = json.loads(await analyze_nutrient_ratios("salmon"))
            assert result["count"] == 1
            assert result["food"] == "Chicken breast"
            assert result["ratios"][0]["name"] == "calcium_to_magnesium"
            assert result["ratios"][0]["status"] == "optimal"

    @pytest.mark.asyncio()
    async def test_no_food_found(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.search_nutrient_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await analyze_nutrient_ratios("nonexistent"))
            assert result["count"] == 0
            assert result["ratios"] == []


class TestComputeInflammatoryIndex:
    @pytest.mark.asyncio()
    async def test_returns_dii(self) -> None:
        dii_result: dict[str, object] = {
            "dii_score": -2.0,
            "classification": "anti-inflammatory",
            "components": {"Fiber, total dietary": -1.0, "Vitamin C": -1.0},
        }
        with (
            patch(
                "ehrlich.nutrition.tools._service.search_nutrient_data",
                new_callable=AsyncMock,
                return_value=[_SAMPLE_PROFILE],
            ),
            patch(
                "ehrlich.nutrition.tools._service.compute_inflammatory_index",
                return_value=dii_result,
            ),
        ):
            result = json.loads(await compute_inflammatory_index("salmon"))
            assert result["food"] == "Chicken breast"
            assert result["classification"] == "anti-inflammatory"
            assert result["dii_score"] == -2.0
            assert "components" in result

    @pytest.mark.asyncio()
    async def test_no_food_found(self) -> None:
        with patch(
            "ehrlich.nutrition.tools._service.search_nutrient_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await compute_inflammatory_index("nonexistent"))
            assert result["classification"] == "neutral"
            assert result["dii_score"] == 0.0
