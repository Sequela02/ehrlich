"""Tests for Sports Science tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.literature.domain.paper import Paper
from ehrlich.sports.domain.entities import (
    AdverseEvent,
    ClinicalTrial,
    IngredientEntry,
    NutrientEntry,
    NutrientProfile,
    SupplementLabel,
)
from ehrlich.sports.tools import (
    analyze_training_evidence,
    assess_injury_risk,
    compare_protocols,
    compute_training_metrics,
    search_clinical_trials,
    search_nutrient_data,
    search_sports_literature,
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
        "ehrlich.sports.tools._client.search",
        new_callable=AsyncMock,
        return_value=papers,
    ) as mock:
        yield mock


class TestSearchSportsLiterature:
    @pytest.mark.asyncio()
    async def test_returns_papers(self, mock_scholar: AsyncMock) -> None:
        result = json.loads(await search_sports_literature("HIIT VO2max"))
        assert result["count"] == 1
        assert result["papers"][0]["title"] == "HIIT vs MICT for VO2max"
        assert result["papers"][0]["doi"] == "10.1234/test"
        mock_scholar.assert_called_once_with("sports science HIIT VO2max", limit=10)

    @pytest.mark.asyncio()
    async def test_custom_limit(self, mock_scholar: AsyncMock) -> None:
        await search_sports_literature("creatine", limit=5)
        mock_scholar.assert_called_once_with("sports science creatine", limit=5)


class TestAnalyzeTrainingEvidence:
    @pytest.mark.asyncio()
    async def test_strong_evidence(self) -> None:
        studies = [
            {"effect_size": 0.8, "sample_size": 30, "quality_score": 0.8},
            {"effect_size": 0.7, "sample_size": 25, "quality_score": 0.75},
            {"effect_size": 0.9, "sample_size": 40, "quality_score": 0.85},
            {"effect_size": 0.75, "sample_size": 35, "quality_score": 0.7},
            {"effect_size": 0.85, "sample_size": 28, "quality_score": 0.9},
        ]
        result = json.loads(
            await analyze_training_evidence("HIIT", "VO2max", studies)
        )
        assert result["study_count"] == 5
        assert result["evidence_grade"] == "A"
        assert result["effect_magnitude"] == "large"
        assert result["pooled_effect_size"] > 0.7

    @pytest.mark.asyncio()
    async def test_limited_evidence(self) -> None:
        studies = [{"effect_size": 0.3, "sample_size": 10, "quality_score": 0.4}]
        result = json.loads(
            await analyze_training_evidence("stretching", "flexibility", studies)
        )
        assert result["evidence_grade"] == "D"

    @pytest.mark.asyncio()
    async def test_empty_studies(self) -> None:
        result = json.loads(
            await analyze_training_evidence("HIIT", "VO2max", [])
        )
        assert "error" in result


class TestCompareProtocols:
    @pytest.mark.asyncio()
    async def test_ranks_protocols(self) -> None:
        protocols = [
            {
                "name": "HIIT",
                "effect_size": 0.8,
                "evidence_quality": 0.9,
                "injury_risk": 0.2,
                "adherence_rate": 0.7,
            },
            {
                "name": "MICT",
                "effect_size": 0.5,
                "evidence_quality": 0.85,
                "injury_risk": 0.1,
                "adherence_rate": 0.9,
            },
        ]
        result = json.loads(await compare_protocols(protocols, "VO2max"))
        assert result["protocol_count"] == 2
        assert result["recommended"] is not None
        assert result["protocols"][0]["rank"] == 1

    @pytest.mark.asyncio()
    async def test_empty_protocols(self) -> None:
        result = json.loads(await compare_protocols([], "VO2max"))
        assert "error" in result


class TestAssessInjuryRisk:
    @pytest.mark.asyncio()
    async def test_low_risk(self) -> None:
        result = json.loads(
            await assess_injury_risk(
                sport="swimming",
                training_load=1.0,
                previous_injuries=[],
                age=25,
                training_history_years=5.0,
            )
        )
        assert result["risk_level"] == "low"
        assert result["risk_score"] < 0.35

    @pytest.mark.asyncio()
    async def test_high_risk(self) -> None:
        result = json.loads(
            await assess_injury_risk(
                sport="football",
                training_load=1.8,
                previous_injuries=["ACL tear", "hamstring strain", "ankle sprain"],
                age=36,
                training_history_years=1.0,
            )
        )
        assert result["risk_level"] == "high"
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio()
    async def test_unknown_sport(self) -> None:
        result = json.loads(
            await assess_injury_risk(
                sport="quidditch",
                training_load=1.0,
                previous_injuries=[],
            )
        )
        assert "risk_score" in result


class TestComputeTrainingMetrics:
    @pytest.mark.asyncio()
    async def test_optimal_acwr(self) -> None:
        daily_loads = [50, 55, 60, 50, 55, 60, 50, 55, 60, 50, 55, 60, 50, 55]
        result = json.loads(await compute_training_metrics(daily_loads))
        assert result["acwr_zone"] == "optimal"
        assert 0.8 <= result["acwr"] <= 1.3

    @pytest.mark.asyncio()
    async def test_too_few_days(self) -> None:
        result = json.loads(await compute_training_metrics([50, 60, 55]))
        assert "error" in result

    @pytest.mark.asyncio()
    async def test_with_rpe(self) -> None:
        loads = [50, 55, 60, 50, 55, 60, 50]
        rpe = [6, 7, 8, 6, 7, 8, 6]
        result = json.loads(await compute_training_metrics(loads, rpe))
        assert "avg_rpe_7d" in result
        assert "session_rpe_load_7d" in result


class TestSearchSupplementEvidence:
    @pytest.mark.asyncio()
    async def test_returns_papers(self, mock_scholar: AsyncMock) -> None:
        result = json.loads(
            await search_supplement_evidence("creatine", "strength")
        )
        assert result["supplement"] == "creatine"
        assert result["outcome"] == "strength"
        assert result["count"] == 1


class TestSearchClinicalTrials:
    @pytest.mark.asyncio()
    async def test_returns_trials(self) -> None:
        trials = [
            ClinicalTrial(
                nct_id="NCT001",
                title="HIIT RCT",
                status="COMPLETED",
                phase="PHASE3",
                enrollment=100,
                conditions=("Exercise",),
                interventions=("HIIT",),
                primary_outcomes=("VO2max change",),
                study_type="INTERVENTIONAL",
                start_date="2023-01-01",
            )
        ]
        with patch(
            "ehrlich.sports.tools._service.search_clinical_trials",
            new_callable=AsyncMock,
            return_value=trials,
        ):
            result = json.loads(await search_clinical_trials("exercise", "HIIT"))
            assert result["count"] == 1
            assert result["trials"][0]["nct_id"] == "NCT001"
            assert result["condition"] == "exercise"

    @pytest.mark.asyncio()
    async def test_empty_results(self) -> None:
        with patch(
            "ehrlich.sports.tools._service.search_clinical_trials",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_clinical_trials("nothing"))
            assert result["count"] == 0


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
            "ehrlich.sports.tools._service.search_supplement_labels",
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
            "ehrlich.sports.tools._service.search_nutrient_data",
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
            "ehrlich.sports.tools._service.search_supplement_safety",
            new_callable=AsyncMock,
            return_value=events,
        ):
            result = json.loads(await search_supplement_safety("pre-workout"))
            assert result["count"] == 1
            assert result["adverse_events"][0]["report_id"] == "FDA-001"
            assert "NAUSEA" in result["adverse_events"][0]["reactions"]
