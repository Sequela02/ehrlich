"""Tests for visualization tools."""

from __future__ import annotations

import json

import pytest

from ehrlich.investigation.tools_viz import (
    render_admet_radar,
    render_binding_scatter,
    render_evidence_matrix,
    render_forest_plot,
    render_muscle_heatmap,
    render_training_timeline,
)


class TestRenderBindingScatter:
    @pytest.mark.asyncio
    async def test_basic_scatter(self) -> None:
        compounds = [
            {"name": "Aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(O)=O", "molecular_weight": 180.16, "binding_affinity": 5.2},
            {"name": "Caffeine", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "molecular_weight": 194.19, "binding_affinity": 3.8},
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
        result = json.loads(
            await render_admet_radar("Ibuprofen", {"absorption": 0.8, "metabolism": 0.6, "toxicity": 0.2})
        )
        assert result["viz_type"] == "admet_radar"
        assert "Ibuprofen" in result["title"]
        assert len(result["data"]["properties"]) == 3
        assert result["config"]["domain"] == "molecular"

    @pytest.mark.asyncio
    async def test_values_clamped(self) -> None:
        result = json.loads(
            await render_admet_radar("Test", {"a": 1.5, "b": -0.3})
        )
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
        assert result["config"]["domain"] == "sports"

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
        assert result["config"]["domain"] == "sports"

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
            {"name": "Study A", "effect_size": 0.5, "ci_lower": 0.2, "ci_upper": 0.8, "weight": 0.6},
            {"name": "Study B", "effect_size": 0.3, "ci_lower": 0.1, "ci_upper": 0.5, "weight": 0.4},
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
