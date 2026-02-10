from __future__ import annotations

import pytest

from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES
from ehrlich.simulation.application.simulation_service import SimulationService
from ehrlich.simulation.infrastructure.pkcsm_client import PkCSMClient
from ehrlich.simulation.infrastructure.protein_store import ProteinStore
from ehrlich.simulation.infrastructure.vina_adapter import VinaAdapter


@pytest.fixture
def service(tmp_path: object) -> SimulationService:
    rdkit = RDKitAdapter()
    return SimulationService(
        protein_store=ProteinStore(proteins_dir=tmp_path),  # type: ignore[arg-type]
        rdkit=rdkit,
        vina=VinaAdapter(),
        admet_client=PkCSMClient(rdkit=rdkit),
    )


class TestDock:
    @pytest.mark.asyncio
    async def test_estimate_fallback(self, service: SimulationService) -> None:
        result = await service.dock(SMILES("c1ccccc1"), "1VQQ")
        assert result.target_id == "1VQQ"
        assert result.binding_energy < 0
        assert "rdkit_estimate" in result.interactions.get("method", [])

    @pytest.mark.asyncio
    async def test_energy_in_reasonable_range(self, service: SimulationService) -> None:
        result = await service.dock(SMILES("CC(=O)Oc1ccccc1C(=O)O"), "1VQQ")
        assert -12.0 <= result.binding_energy <= -2.0


class TestPredictADMET:
    @pytest.mark.asyncio
    async def test_returns_full_profile(self, service: SimulationService) -> None:
        profile = await service.predict_admet(SMILES("CC(=O)Oc1ccccc1C(=O)O"))
        assert profile.qed > 0
        assert profile.lipinski_violations == 0
        assert not profile.has_toxicity_flags


class TestAssessResistance:
    @pytest.mark.asyncio
    async def test_known_target_has_mutations(self, service: SimulationService) -> None:
        result = await service.assess_resistance(SMILES("c1ccccc1"), "1VQQ")
        assert result.target_id == "1VQQ"
        assert result.target_name == "PBP2a"
        assert len(result.mutation_risks) == 2
        assert result.risk_level in ("LOW", "MODERATE", "HIGH")

    @pytest.mark.asyncio
    async def test_dna_gyrase_mutations(self, service: SimulationService) -> None:
        result = await service.assess_resistance(SMILES("c1ccccc1"), "2XCT")
        assert result.target_name == "DNA Gyrase"
        assert len(result.mutation_risks) == 1
        assert result.mutation_risks[0].mutation == "S84L"

    @pytest.mark.asyncio
    async def test_mutations_dict_populated(self, service: SimulationService) -> None:
        result = await service.assess_resistance(SMILES("c1ccccc1"), "1VQQ")
        assert "S403A" in result.mutations
        assert "N146K" in result.mutations
