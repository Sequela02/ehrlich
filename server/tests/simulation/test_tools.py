from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.kernel.types import SMILES
from ehrlich.simulation.domain.admet_profile import ADMETProfile
from ehrlich.simulation.domain.docking_result import DockingResult
from ehrlich.simulation.domain.resistance_assessment import (
    MutationRisk,
    ResistanceAssessment,
)


class TestDockTool:
    @pytest.mark.asyncio
    async def test_returns_json_with_energy(self) -> None:
        from ehrlich.simulation import tools

        mock_result = DockingResult(
            smiles=SMILES("c1ccccc1"),
            target_id="1VQQ",
            binding_energy=-7.5,
            pose_rmsd=0.0,
            interactions={"method": ["rdkit_estimate"]},
        )
        with patch.object(tools._service, "dock", new_callable=AsyncMock) as mock:
            mock.return_value = mock_result
            result = json.loads(await tools.dock_against_target("c1ccccc1", "1VQQ"))
            assert result["binding_energy"] == -7.5
            assert result["target_id"] == "1VQQ"


class TestADMETTool:
    @pytest.mark.asyncio
    async def test_returns_json_with_profile(self) -> None:
        from ehrlich.simulation import tools

        mock_profile = ADMETProfile(
            absorption=100.0,
            qed=0.55,
            lipinski_violations=0,
            toxicity_ames=False,
            herg_inhibitor=False,
        )
        with patch.object(tools._service, "predict_admet", new_callable=AsyncMock) as mock:
            mock.return_value = mock_profile
            result = json.loads(await tools.predict_admet("CCO"))
            assert result["absorption"] == 100.0
            assert result["qed"] == 0.55
            assert result["has_toxicity_flags"] is False


class TestResistanceTool:
    @pytest.mark.asyncio
    async def test_returns_json_with_mutations(self) -> None:
        from ehrlich.simulation import tools

        mock_result = ResistanceAssessment(
            target_id="1VQQ",
            target_name="PBP2a",
            risk_level="HIGH",
            mutation_risks=(
                MutationRisk(
                    mutation="S403A", risk_level="HIGH", mechanism="Beta-lactam resistance"
                ),
            ),
            mutations={"S403A": "HIGH"},
            explanation="Assessment for PBP2a: 1 known resistance mutation(s).",
        )
        with patch.object(tools._service, "assess_resistance", new_callable=AsyncMock) as mock:
            mock.return_value = mock_result
            result = json.loads(await tools.assess_resistance("c1ccccc1", "1VQQ"))
            assert result["risk_level"] == "HIGH"
            assert result["target_name"] == "PBP2a"
            assert len(result["mutation_details"]) == 1
            assert result["mutation_details"][0]["mutation"] == "S403A"
