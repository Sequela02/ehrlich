from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.kernel.types import SMILES
from ehrlich.simulation.domain.admet_profile import ADMETProfile
from ehrlich.simulation.domain.docking_result import DockingResult
from ehrlich.simulation.domain.protein_target import ProteinTarget
from ehrlich.simulation.domain.resistance_assessment import (
    MutationRisk,
    ResistanceAssessment,
)
from ehrlich.simulation.domain.toxicity_profile import ToxicityProfile


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


class TestSearchProteinTargets:
    @pytest.mark.asyncio
    async def test_returns_targets_json(self) -> None:
        from ehrlich.simulation import tools

        mock_targets = [
            ProteinTarget(
                pdb_id="1VQQ",
                name="PBP2a",
                organism="Staphylococcus aureus",
                center_x=26.0,
                center_y=13.0,
                center_z=60.0,
                box_size=22.0,
            ),
        ]
        with patch.object(tools._service, "search_targets", new_callable=AsyncMock) as mock:
            mock.return_value = mock_targets
            result = json.loads(await tools.search_protein_targets("PBP2a", "Staphylococcus"))
            assert result["count"] == 1
            assert result["query"] == "PBP2a"
            assert result["organism"] == "Staphylococcus"
            assert result["targets"][0]["pdb_id"] == "1VQQ"
            assert result["targets"][0]["name"] == "PBP2a"
            assert result["targets"][0]["center"] == [26.0, 13.0, 60.0]

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        from ehrlich.simulation import tools

        with patch.object(tools._service, "search_targets", new_callable=AsyncMock) as mock:
            mock.return_value = []
            result = json.loads(await tools.search_protein_targets("nonexistent"))
            assert result["count"] == 0
            assert result["targets"] == []

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        from ehrlich.kernel.exceptions import ExternalServiceError
        from ehrlich.simulation import tools

        with patch.object(tools._service, "search_targets", new_callable=AsyncMock) as mock:
            mock.side_effect = ExternalServiceError("RCSB PDB", "timeout")
            result = json.loads(await tools.search_protein_targets("test"))
            assert "error" in result


class TestFetchToxicityProfile:
    @pytest.mark.asyncio
    async def test_returns_profile_json(self) -> None:
        from ehrlich.simulation import tools

        mock_profile = ToxicityProfile(
            dtxsid="DTXSID7020182",
            name="bisphenol a",
            casrn="80-05-7",
            molecular_weight=228.29,
            oral_rat_ld50=3250.0,
            lc50_fish=4.7,
            bioconcentration_factor=70.8,
            developmental_toxicity=True,
            mutagenicity=False,
        )
        with patch.object(tools._service, "fetch_toxicity", new_callable=AsyncMock) as mock:
            mock.return_value = mock_profile
            result = json.loads(await tools.fetch_toxicity_profile("bisphenol a"))
            assert result["dtxsid"] == "DTXSID7020182"
            assert result["oral_rat_ld50"] == 3250.0
            assert result["developmental_toxicity"] is True
            assert result["mutagenicity"] is False
            assert result["source"] == "epa_comptox"

    @pytest.mark.asyncio
    async def test_no_data_returns_message(self) -> None:
        from ehrlich.simulation import tools

        with patch.object(tools._service, "fetch_toxicity", new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = json.loads(await tools.fetch_toxicity_profile("unknown"))
            assert "message" in result
            assert result["identifier"] == "unknown"

    @pytest.mark.asyncio
    async def test_error_handling(self) -> None:
        from ehrlich.kernel.exceptions import ExternalServiceError
        from ehrlich.simulation import tools

        with patch.object(tools._service, "fetch_toxicity", new_callable=AsyncMock) as mock:
            mock.side_effect = ExternalServiceError("EPA CompTox", "timeout")
            result = json.loads(await tools.fetch_toxicity_profile("test"))
            assert "error" in result
