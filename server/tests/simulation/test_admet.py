from __future__ import annotations

import pytest

from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES
from ehrlich.simulation.infrastructure.pkcsm_client import PkCSMClient


@pytest.fixture
def client() -> PkCSMClient:
    return PkCSMClient(rdkit=RDKitAdapter())


class TestPredictADMET:
    @pytest.mark.asyncio
    async def test_aspirin_profile(self, client: PkCSMClient) -> None:
        profile = await client.predict(SMILES("CC(=O)Oc1ccccc1C(=O)O"))
        assert profile.lipinski_violations == 0
        assert profile.qed > 0
        assert profile.absorption > 0
        assert not profile.toxicity_ames
        assert not profile.herg_inhibitor

    @pytest.mark.asyncio
    async def test_ethanol_bbb_permeant(self, client: PkCSMClient) -> None:
        profile = await client.predict(SMILES("CCO"))
        assert profile.lipinski_violations == 0
        assert profile.absorption == 100.0

    @pytest.mark.asyncio
    async def test_nitroaromatic_mutagenic(self, client: PkCSMClient) -> None:
        profile = await client.predict(SMILES("c1ccc(cc1)[N+](=O)[O-]"))
        assert profile.toxicity_ames is True
        assert profile.has_toxicity_flags is True

    @pytest.mark.asyncio
    async def test_large_lipophilic_hepatotoxic(self, client: PkCSMClient) -> None:
        # Large lipophilic compound: LogP > 3.5 and MW > 400
        smiles = SMILES("CCCCCCCCCCCCCCCCCCOC(=O)c1ccccc1OC(=O)CCCCCCCCCCCCCC")
        profile = await client.predict(smiles)
        assert profile.hepatotoxicity is True

    @pytest.mark.asyncio
    async def test_no_none_values(self, client: PkCSMClient) -> None:
        profile = await client.predict(SMILES("c1ccccc1"))
        assert profile.absorption is not None
        assert profile.distribution_vd is not None
        assert profile.excretion_clearance is not None
        assert profile.toxicity_ld50 is not None
        assert profile.qed is not None
