"""Tests for visualization tools."""

from __future__ import annotations

import json

import pytest

from ehrlich.investigation.tools_viz import (
    render_admet_radar,
    render_binding_scatter,
    render_dose_response,
    render_evidence_matrix,
    render_forest_plot,
    render_funnel_plot,
    render_muscle_heatmap,
    render_nutrient_adequacy,
    render_nutrient_comparison,
    render_performance_chart,
    render_therapeutic_window,
    render_training_timeline,
)


class TestRenderBindingScatter:
    @pytest.mark.asyncio
    async def test_basic_scatter(self) -> None:
        compounds = [
            {
                "name": "Aspirin",
                "smiles": "CC(=O)OC1=CC=CC=C1C(O)=O",
                "molecular_weight": 180.16,
                "binding_affinity": 5.2,
            },
            {
                "name": "Caffeine",
                "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                "molecular_weight": 194.19,
                "binding_affinity": 3.8,
            },
        ]
        result = json.loads(await render_binding_scatter(compounds))
        assert result["viz_type"] == "binding_scatter"
        assert result["title"] == "Binding Affinity Landscape"
        assert len(result["data"]["points"]) == 2
        assert result["data"]["x_label"] == "molecular_weight"
        assert result["data"]["y_label"] == "binding_affinity"
        assert result["config"]["domain"] == "molecular"

    @pytest.mark.asyncio
    async def test_custom_axes(self) -> None:
        compounds = [{"name": "A", "logp": 2.5, "tpsa": 40.0}]
        result = json.loads(
            await render_binding_scatter(compounds, x_property="logp", y_property="tpsa")
        )
        assert result["data"]["x_label"] == "logp"
        assert result["data"]["y_label"] == "tpsa"

    @pytest.mark.asyncio
    async def test_empty_compounds(self) -> None:
        result = json.loads(await render_binding_scatter([]))
        assert result["data"]["points"] == []


class TestRenderADMETRadar:
    @pytest.mark.asyncio
    async def test_basic_radar(self) -> None:
        props = {"absorption": 0.8, "metabolism": 0.6, "toxicity": 0.2}
        result = json.loads(await render_admet_radar("Ibuprofen", props))
        assert result["viz_type"] == "admet_radar"
        assert "Ibuprofen" in result["title"]
        assert len(result["data"]["properties"]) == 3
        assert result["config"]["domain"] == "molecular"

    @pytest.mark.asyncio
    async def test_values_clamped(self) -> None:
        result = json.loads(await render_admet_radar("Test", {"a": 1.5, "b": -0.3}))
        props = {p["axis"]: p["value"] for p in result["data"]["properties"]}
        assert props["a"] == 1.0
        assert props["b"] == 0.0


class TestRenderTrainingTimeline:
    @pytest.mark.asyncio
    async def test_basic_timeline(self) -> None:
        daily_loads = [
            {"date": "2026-01-01", "load": 300},
            {"date": "2026-01-02", "load": 400, "rpe": 7},
            {"date": "2026-01-03", "load": 350, "duration_min": 60},
        ]
        result = json.loads(await render_training_timeline(daily_loads))
        assert result["viz_type"] == "training_timeline"
        assert len(result["data"]["timeline"]) == 3
        assert len(result["data"]["acwr"]) == 3
        assert len(result["data"]["danger_zones"]) == 2
        assert result["config"]["domain"] == "training"

    @pytest.mark.asyncio
    async def test_acwr_computation(self) -> None:
        loads = [{"date": f"2026-01-{i:02d}", "load": 100.0} for i in range(1, 8)]
        result = json.loads(await render_training_timeline(loads))
        last_acwr = result["data"]["acwr"][-1]["acwr"]
        assert last_acwr == pytest.approx(1.0, abs=0.01)


class TestRenderMuscleHeatmap:
    @pytest.mark.asyncio
    async def test_basic_heatmap(self) -> None:
        muscles = [
            {"muscle": "quadriceps", "intensity": 0.8},
            {"muscle": "hamstrings", "intensity": 0.6},
        ]
        result = json.loads(await render_muscle_heatmap(muscles))
        assert result["viz_type"] == "muscle_heatmap"
        assert result["data"]["view"] == "front"
        assert len(result["data"]["muscles"]) == 2
        assert result["config"]["domain"] == "training"

    @pytest.mark.asyncio
    async def test_known_muscle_flagged(self) -> None:
        muscles = [
            {"muscle": "quadriceps", "intensity": 0.5},
            {"muscle": "unknown_muscle", "intensity": 0.3},
        ]
        result = json.loads(await render_muscle_heatmap(muscles))
        known = {m["muscle"]: m["known"] for m in result["data"]["muscles"]}
        assert known["quadriceps"] is True
        assert known["unknown_muscle"] is False

    @pytest.mark.asyncio
    async def test_invalid_view_defaults_front(self) -> None:
        result = json.loads(await render_muscle_heatmap([], view="invalid"))
        assert result["data"]["view"] == "front"


class TestRenderForestPlot:
    @pytest.mark.asyncio
    async def test_basic_forest(self) -> None:
        studies = [
            {
                "name": "Study A",
                "effect_size": 0.5,
                "ci_lower": 0.2,
                "ci_upper": 0.8,
                "weight": 0.6,
            },
            {
                "name": "Study B",
                "effect_size": 0.3,
                "ci_lower": 0.1,
                "ci_upper": 0.5,
                "weight": 0.4,
            },
        ]
        result = json.loads(await render_forest_plot(studies))
        assert result["viz_type"] == "forest_plot"
        assert len(result["data"]["studies"]) == 2
        assert "pooled" in result["data"]
        assert result["data"]["effect_measure"] == "SMD"

    @pytest.mark.asyncio
    async def test_pooled_calculation(self) -> None:
        studies = [
            {"name": "A", "effect_size": 1.0, "ci_lower": 0.0, "ci_upper": 2.0, "weight": 1.0},
        ]
        result = json.loads(await render_forest_plot(studies))
        assert result["data"]["pooled"]["effect_size"] == 1.0

    @pytest.mark.asyncio
    async def test_empty_studies(self) -> None:
        result = json.loads(await render_forest_plot([]))
        assert result["data"]["pooled"]["effect_size"] == 0.0


class TestRenderEvidenceMatrix:
    @pytest.mark.asyncio
    async def test_basic_matrix(self) -> None:
        result = json.loads(
            await render_evidence_matrix(
                hypotheses=["H1", "H2"],
                evidence_sources=["ChEMBL", "PubChem"],
                matrix=[[0.8, -0.3], [0.0, 0.6]],
            )
        )
        assert result["viz_type"] == "evidence_matrix"
        assert result["data"]["rows"] == ["H1", "H2"]
        assert result["data"]["cols"] == ["ChEMBL", "PubChem"]
        assert result["data"]["values"][0][0] == 0.8
        assert result["config"]["color_scale"] == "diverging"

    @pytest.mark.asyncio
    async def test_values_clamped(self) -> None:
        result = json.loads(
            await render_evidence_matrix(
                hypotheses=["H1"],
                evidence_sources=["S1"],
                matrix=[[2.5]],
            )
        )
        assert result["data"]["values"][0][0] == 1.0


class TestRenderPerformanceChart:
    @pytest.mark.asyncio
    async def test_basic_chart(self) -> None:
        data = [
            {"day": 1, "fitness": 10.0, "fatigue": 15.0, "form": -5.0},
            {"day": 2, "fitness": 12.0, "fatigue": 14.0, "form": -2.0},
            {"day": 3, "fitness": 15.0, "fatigue": 10.0, "form": 5.0},
        ]
        result = json.loads(await render_performance_chart(data))
        assert result["viz_type"] == "performance_chart"
        assert len(result["data"]["points"]) == 3
        assert result["data"]["peak_form"] == 5.0
        assert result["config"]["domain"] == "training"

    @pytest.mark.asyncio
    async def test_empty_data(self) -> None:
        result = json.loads(await render_performance_chart([]))
        assert result["data"]["points"] == []


class TestRenderFunnelPlot:
    @pytest.mark.asyncio
    async def test_basic_funnel(self) -> None:
        studies = [
            {"name": "Study A", "effect_size": 0.5, "se": 0.1, "sample_size": 100},
            {"name": "Study B", "effect_size": 0.3, "se": 0.2, "sample_size": 50},
            {"name": "Study C", "effect_size": 0.6, "se": 0.15, "sample_size": 75},
        ]
        result = json.loads(await render_funnel_plot(studies))
        assert result["viz_type"] == "funnel_plot"
        assert len(result["data"]["studies"]) == 3
        assert "pooled_effect" in result["data"]
        assert len(result["data"]["funnel_bounds"]) == 5

    @pytest.mark.asyncio
    async def test_empty_studies(self) -> None:
        result = json.loads(await render_funnel_plot([]))
        assert result["data"]["studies"] == []


class TestRenderDoseResponse:
    @pytest.mark.asyncio
    async def test_basic_curve(self) -> None:
        points = [
            {"dose": 10, "effect": -0.2, "ci_lower": -0.3, "ci_upper": -0.1},
            {"dose": 5, "effect": -0.1, "ci_lower": -0.2, "ci_upper": 0.0},
            {"dose": 20, "effect": -0.25, "ci_lower": -0.35, "ci_upper": -0.15},
        ]
        result = json.loads(await render_dose_response(points, dose_label="MET-h/wk"))
        assert result["viz_type"] == "dose_response"
        assert len(result["data"]["points"]) == 3
        assert result["data"]["points"][0]["dose"] == 5  # sorted by dose
        assert result["data"]["dose_label"] == "MET-h/wk"
        assert result["config"]["domain"] == "training"

    @pytest.mark.asyncio
    async def test_empty_points(self) -> None:
        result = json.loads(await render_dose_response([]))
        assert result["data"]["points"] == []


class TestRenderNutrientComparison:
    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        foods = [
            {
                "name": "Chicken breast",
                "nutrients": [
                    {"name": "Protein", "amount": 31, "unit": "g", "pct_rda": 0.62},
                    {"name": "Iron", "amount": 1.0, "unit": "mg", "pct_rda": 0.13},
                ],
            },
            {
                "name": "Salmon",
                "nutrients": [
                    {"name": "Protein", "amount": 25, "unit": "g", "pct_rda": 0.50},
                    {"name": "Iron", "amount": 0.8, "unit": "mg", "pct_rda": 0.10},
                ],
            },
        ]
        result = json.loads(await render_nutrient_comparison(foods))
        assert result["viz_type"] == "nutrient_comparison"
        assert len(result["data"]["foods"]) == 2
        assert set(result["data"]["nutrient_labels"]) == {"Protein", "Iron"}
        assert result["config"]["domain"] == "nutrition"

    @pytest.mark.asyncio
    async def test_empty(self) -> None:
        result = json.loads(await render_nutrient_comparison([]))
        assert result["data"]["foods"] == []
        assert result["data"]["nutrient_labels"] == []

    @pytest.mark.asyncio
    async def test_with_filter(self) -> None:
        foods = [
            {
                "name": "Egg",
                "nutrients": [
                    {"name": "Protein", "amount": 6, "unit": "g", "pct_rda": 0.12},
                    {"name": "Vitamin D", "amount": 1.1, "unit": "mcg", "pct_rda": 0.07},
                ],
            },
        ]
        result = json.loads(await render_nutrient_comparison(foods, nutrients=["Protein"]))
        assert result["data"]["nutrient_labels"] == ["Protein"]
        assert len(result["data"]["foods"][0]["nutrients"]) == 1


class TestRenderNutrientAdequacy:
    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        data = [
            {"name": "Vitamin C", "pct_rda": 1.2, "intake": 108, "rda": 90, "unit": "mg"},
            {"name": "Vitamin D", "pct_rda": 0.4, "intake": 6, "rda": 15, "unit": "mcg"},
        ]
        result = json.loads(await render_nutrient_adequacy(data))
        assert result["viz_type"] == "nutrient_adequacy"
        assert len(result["data"]["nutrients"]) == 2
        assert result["config"]["domain"] == "nutrition"

    @pytest.mark.asyncio
    async def test_mar_computation(self) -> None:
        data = [
            {"name": "A", "pct_rda": 1.5, "intake": 0, "rda": 1, "unit": "mg"},
            {"name": "B", "pct_rda": 0.5, "intake": 0, "rda": 1, "unit": "mg"},
        ]
        result = json.loads(await render_nutrient_adequacy(data))
        # MAR = mean(min(1.5, 1.0), min(0.5, 1.0)) = (1.0 + 0.5) / 2 = 0.75
        assert result["data"]["mar_score"] == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_status_assignment(self) -> None:
        data = [
            {"name": "Low", "pct_rda": 0.3, "intake": 0, "rda": 1, "unit": "mg"},
            {"name": "Mid", "pct_rda": 0.6, "intake": 0, "rda": 1, "unit": "mg"},
            {"name": "High", "pct_rda": 0.9, "intake": 0, "rda": 1, "unit": "mg"},
        ]
        result = json.loads(await render_nutrient_adequacy(data))
        statuses = {n["name"]: n["status"] for n in result["data"]["nutrients"]}
        assert statuses["Low"] == "deficient"
        assert statuses["Mid"] == "inadequate"
        assert statuses["High"] == "adequate"


class TestRenderTherapeuticWindow:
    @pytest.mark.asyncio
    async def test_basic(self) -> None:
        nutrients = [
            {
                "name": "Vitamin C",
                "ear": 75,
                "rda": 90,
                "ul": 2000,
                "current_intake": 100,
                "unit": "mg",
            },
        ]
        result = json.loads(await render_therapeutic_window(nutrients))
        assert result["viz_type"] == "therapeutic_window"
        assert len(result["data"]["nutrients"]) == 1
        assert result["config"]["domain"] == "nutrition"

    @pytest.mark.asyncio
    async def test_zone_computation(self) -> None:
        nutrients = [
            {
                "name": "Deficient",
                "ear": 100,
                "rda": 150,
                "ul": 500,
                "current_intake": 50,
                "unit": "mg",
            },
            {
                "name": "Inadequate",
                "ear": 100,
                "rda": 150,
                "ul": 500,
                "current_intake": 120,
                "unit": "mg",
            },
            {
                "name": "Adequate",
                "ear": 100,
                "rda": 150,
                "ul": 500,
                "current_intake": 200,
                "unit": "mg",
            },
            {
                "name": "Excessive",
                "ear": 100,
                "rda": 150,
                "ul": 500,
                "current_intake": 600,
                "unit": "mg",
            },
        ]
        result = json.loads(await render_therapeutic_window(nutrients))
        zones = {n["name"]: n["zone"] for n in result["data"]["nutrients"]}
        assert zones["Deficient"] == "deficient"
        assert zones["Inadequate"] == "inadequate"
        assert zones["Adequate"] == "adequate"
        assert zones["Excessive"] == "excessive"
