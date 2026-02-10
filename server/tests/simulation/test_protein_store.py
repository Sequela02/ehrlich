from __future__ import annotations

import pytest

from ehrlich.kernel.exceptions import TargetNotFoundError
from ehrlich.simulation.infrastructure.protein_store import ProteinStore


@pytest.fixture
def store(tmp_path: object) -> ProteinStore:
    return ProteinStore(proteins_dir=tmp_path)  # type: ignore[arg-type]


class TestGetTarget:
    def test_known_target(self, store: ProteinStore) -> None:
        target = store.get_target("1VQQ")
        assert target.pdb_id == "1VQQ"
        assert target.name == "PBP2a"
        assert target.center_x != 0.0

    def test_case_insensitive(self, store: ProteinStore) -> None:
        target = store.get_target("1vqq")
        assert target.pdb_id == "1VQQ"

    def test_unknown_raises(self, store: ProteinStore) -> None:
        with pytest.raises(TargetNotFoundError):
            store.get_target("XXXX")

    def test_all_targets_have_coordinates(self, store: ProteinStore) -> None:
        targets = ["1VQQ", "1AD4", "2XCT", "1UAE", "3SPU"]
        for pdb_id in targets:
            target = store.get_target(pdb_id)
            assert target.box_size > 0


class TestListTargets:
    @pytest.mark.asyncio
    async def test_returns_five_targets(self, store: ProteinStore) -> None:
        targets = await store.list_targets()
        assert len(targets) == 5
        pdb_ids = {t.pdb_id for t in targets}
        assert pdb_ids == {"1VQQ", "1AD4", "2XCT", "1UAE", "3SPU"}


class TestGetPDBQT:
    @pytest.mark.asyncio
    async def test_missing_file_raises(self, store: ProteinStore) -> None:
        with pytest.raises(FileNotFoundError, match="PDBQT file not found"):
            await store.get_pdbqt("1VQQ")
