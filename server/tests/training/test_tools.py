"""Tests for Training Science tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.literature.domain.paper import Paper
from ehrlich.training.domain.entities import ClinicalTrial
from ehrlich.training.tools import (
    analyze_training_evidence,
    assess_injury_risk,
    compare_protocols,
    compute_dose_response,
    compute_performance_model,
    compute_training_metrics,
    plan_periodization,
    search_clinical_trials,
    search_exercise_database,
    search_pubmed_training,
    search_training_literature,
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
        "ehrlich.training.tools._client.search",
        new_callable=AsyncMock,
        return_value=papers,
    ) as mock:
        yield mock


class TestSearchTrainingLiterature:
    @pytest.mark.asyncio()
    async def test_returns_papers(self, mock_scholar: AsyncMock) -> None:
        result = json.loads(await search_training_literature("HIIT VO2max"))
        assert result["count"] == 1
        assert result["papers"][0]["title"] == "HIIT vs MICT for VO2max"
        assert result["papers"][0]["doi"] == "10.1234/test"
        mock_scholar.assert_called_once_with("training science HIIT VO2max", limit=10)

    @pytest.mark.asyncio()
    async def test_custom_limit(self, mock_scholar: AsyncMock) -> None:
        await search_training_literature("creatine", limit=5)
        mock_scholar.assert_called_once_with("training science creatine", limit=5)


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
        result = json.loads(await analyze_training_evidence("HIIT", "VO2max", studies))
        assert result["study_count"] == 5
        assert result["evidence_grade"] == "A"
        assert result["effect_magnitude"] == "large"
        assert result["pooled_effect_size"] > 0.7

    @pytest.mark.asyncio()
    async def test_limited_evidence(self) -> None:
        studies = [{"effect_size": 0.3, "sample_size": 10, "quality_score": 0.4}]
        result = json.loads(await analyze_training_evidence("stretching", "flexibility", studies))
        assert result["evidence_grade"] == "D"

    @pytest.mark.asyncio()
    async def test_empty_studies(self) -> None:
        result = json.loads(await analyze_training_evidence("HIIT", "VO2max", []))
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
    @pytest.fixture(autouse=True)
    def _no_pubmed(self):
        with patch(
            "ehrlich.training.tools._service._pubmed.search",
            new_callable=AsyncMock,
            return_value=[],
        ):
            yield

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
        assert result["epidemiological_context"] == []

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
        assert result["epidemiological_context"] == []

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
        assert "epidemiological_context" in result

    @pytest.mark.asyncio()
    async def test_with_pubmed_context(self) -> None:
        from ehrlich.training.domain.entities import PubMedArticle

        articles = [
            PubMedArticle(
                pmid="99001",
                title="Injury incidence in soccer: a systematic review",
                abstract="Review of soccer injury rates.",
                authors=("Lopez A",),
                journal="Br J Sports Med",
                year=2024,
                doi="10.1136/test",
                mesh_terms=("Athletic Injuries",),
                publication_type="Review",
            ),
        ]
        with patch(
            "ehrlich.training.tools._service._pubmed.search",
            new_callable=AsyncMock,
            return_value=articles,
        ):
            result = json.loads(
                await assess_injury_risk(
                    sport="soccer",
                    training_load=1.0,
                    previous_injuries=[],
                )
            )
        ctx = result["epidemiological_context"]
        assert len(ctx) == 1
        assert ctx[0]["pmid"] == "99001"
        assert ctx[0]["title"] == "Injury incidence in soccer: a systematic review"
        assert ctx[0]["year"] == "2024"
        assert "soccer" in ctx[0]["relevance_note"]


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
            "ehrlich.training.tools._service.search_clinical_trials",
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
            "ehrlich.training.tools._service.search_clinical_trials",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_clinical_trials("nothing"))
            assert result["count"] == 0


class TestSearchPubmedTraining:
    @pytest.mark.asyncio()
    async def test_returns_articles(self) -> None:
        from ehrlich.training.domain.entities import PubMedArticle

        articles = [
            PubMedArticle(
                pmid="12345",
                title="HIIT meta-analysis",
                abstract="This is the abstract.",
                authors=("Smith J",),
                journal="J Sports Med",
                year=2024,
                doi="10.1234/test",
                mesh_terms=("Exercise",),
                publication_type="Journal Article",
            )
        ]
        with patch(
            "ehrlich.training.tools._service.search_pubmed",
            new_callable=AsyncMock,
            return_value=articles,
        ):
            result = json.loads(await search_pubmed_training("HIIT"))
            assert result["count"] == 1
            assert result["articles"][0]["pmid"] == "12345"

    @pytest.mark.asyncio()
    async def test_empty_results(self) -> None:
        with patch(
            "ehrlich.training.tools._service.search_pubmed",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_pubmed_training("nothing"))
            assert result["count"] == 0


class TestSearchExerciseDatabase:
    @pytest.mark.asyncio()
    async def test_returns_exercises(self) -> None:
        from ehrlich.training.domain.entities import Exercise

        exercises = [
            Exercise(
                id=1,
                name="Bench Press",
                category="Chest",
                muscles_primary=("Pectoralis major",),
                muscles_secondary=("Triceps",),
                equipment=("Barbell",),
                description="Lie on bench and press.",
            )
        ]
        with patch(
            "ehrlich.training.tools._service.search_exercises",
            new_callable=AsyncMock,
            return_value=exercises,
        ):
            result = json.loads(await search_exercise_database(muscle_group="chest"))
            assert result["count"] == 1
            assert result["exercises"][0]["name"] == "Bench Press"

    @pytest.mark.asyncio()
    async def test_empty_results(self) -> None:
        with patch(
            "ehrlich.training.tools._service.search_exercises",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_exercise_database())
            assert result["count"] == 0


class TestComputePerformanceModel:
    @pytest.mark.asyncio()
    async def test_returns_model(self) -> None:
        loads = [50.0] * 20
        result = json.loads(await compute_performance_model(loads))
        assert result["days"] == 20
        assert result["fitness_tau"] == 42
        assert result["fatigue_tau"] == 7
        assert len(result["model"]) == 20
        assert "peak_form_day" in result

    @pytest.mark.asyncio()
    async def test_too_few_days(self) -> None:
        result = json.loads(await compute_performance_model([50.0] * 5))
        assert "error" in result


class TestComputeDoseResponse:
    @pytest.mark.asyncio()
    async def test_returns_curve(self) -> None:
        result = json.loads(
            await compute_dose_response(
                dose_levels=[5.0, 10.0, 15.0],
                effect_sizes=[-0.1, -0.2, -0.25],
                ci_lower=[-0.2, -0.3, -0.35],
                ci_upper=[0.0, -0.1, -0.15],
            )
        )
        assert result["point_count"] == 3
        assert result["points"][0]["dose"] == 5.0  # sorted

    @pytest.mark.asyncio()
    async def test_too_few_levels(self) -> None:
        result = json.loads(
            await compute_dose_response(
                dose_levels=[5.0],
                effect_sizes=[-0.1],
                ci_lower=[-0.2],
                ci_upper=[0.0],
            )
        )
        assert "error" in result


class TestPlanPeriodization:
    @pytest.mark.asyncio()
    async def test_linear_model(self) -> None:
        result = json.loads(await plan_periodization("strength", total_weeks=12, model="linear"))
        assert result["model"] == "linear"
        assert result["total_weeks"] == 12
        assert len(result["blocks"]) == 3
        # Intensity should increase across blocks
        blocks = result["blocks"]
        assert blocks[0]["intensity_range"][1] < blocks[2]["intensity_range"][0]

    @pytest.mark.asyncio()
    async def test_undulating_model(self) -> None:
        result = json.loads(
            await plan_periodization("hypertrophy", total_weeks=8, model="undulating")
        )
        assert result["model"] == "undulating"
        assert len(result["blocks"]) == 1
        assert result["blocks"][0]["name"] == "Undulating"
        assert len(result["weekly_load_progression"]) == 8

    @pytest.mark.asyncio()
    async def test_block_model(self) -> None:
        result = json.loads(await plan_periodization("power", total_weeks=12, model="block"))
        assert result["model"] == "block"
        phase_types = [b["phase_type"] for b in result["blocks"]]
        assert "accumulation" in phase_types
        assert "transmutation" in phase_types
        assert "realization" in phase_types

    @pytest.mark.asyncio()
    async def test_short_plan(self) -> None:
        result = json.loads(
            await plan_periodization("general fitness", total_weeks=4, model="linear")
        )
        assert result["total_weeks"] == 4
        total_block_weeks = sum(b["weeks"] for b in result["blocks"])
        assert total_block_weeks == 4

    @pytest.mark.asyncio()
    async def test_invalid_model(self) -> None:
        result = json.loads(await plan_periodization("strength", model="conjugate"))
        assert "error" in result

    @pytest.mark.asyncio()
    async def test_deload_weeks(self) -> None:
        result = json.loads(await plan_periodization("strength", total_weeks=12, model="block"))
        progression = result["weekly_load_progression"]
        assert len(progression) == 12
        # Every 4th week should be a deload (lower than surrounding weeks)
        for i in range(len(progression)):
            if (i + 1) % 4 == 0:
                # Deload weeks should be notably lower
                assert progression[i] < 0.60
