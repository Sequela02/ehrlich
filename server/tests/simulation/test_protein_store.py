from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from ehrlich.kernel.exceptions import TargetNotFoundError
from ehrlich.simulation.infrastructure.protein_store import ProteinStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def store(tmp_path: Path) -> ProteinStore:
    return ProteinStore(proteins_dir=tmp_path)


@pytest.fixture
def custom_store(tmp_path: Path) -> ProteinStore:
    yaml_data = {
        "targets": [
            {
                "pdb_id": "9ABC",
                "name": "Custom Target",
                "organism": "Homo sapiens",
                "center_x": 10.0,
                "center_y": 20.0,
                "center_z": 30.0,
                "box_size": 18.0,
            }
        ]
    }
    yaml_path = tmp_path / "custom.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_data, f)
    return ProteinStore(proteins_dir=tmp_path, yaml_path=yaml_path)


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


class TestYAMLLoading:
    def test_custom_yaml_loaded(self, custom_store: ProteinStore) -> None:
        target = custom_store.get_target("9ABC")
        assert target.name == "Custom Target"
        assert target.organism == "Homo sapiens"
        assert target.center_x == 10.0
        assert target.box_size == 18.0

    def test_custom_yaml_replaces_defaults(self, custom_store: ProteinStore) -> None:
        with pytest.raises(TargetNotFoundError):
            custom_store.get_target("1VQQ")

    @pytest.mark.asyncio
    async def test_custom_yaml_list(self, custom_store: ProteinStore) -> None:
        targets = await custom_store.list_targets()
        assert len(targets) == 1
        assert targets[0].pdb_id == "9ABC"

    def test_missing_yaml_gives_empty(self, tmp_path: Path) -> None:
        store = ProteinStore(proteins_dir=tmp_path, yaml_path=tmp_path / "nonexistent.yaml")
        with pytest.raises(TargetNotFoundError):
            store.get_target("1VQQ")


class TestSearch:
    @pytest.mark.asyncio
    async def test_local_search_by_name(self, store: ProteinStore) -> None:
        results = await store.search("PBP2a")
        assert len(results) >= 1
        assert results[0].pdb_id == "1VQQ"

    @pytest.mark.asyncio
    async def test_local_search_by_organism(self, store: ProteinStore) -> None:
        results = await store.search("Escherichia")
        assert len(results) >= 1
        assert results[0].pdb_id == "1UAE"

    @pytest.mark.asyncio
    async def test_local_search_no_match(self, store: ProteinStore) -> None:
        results = await store.search("nonexistent_protein_xyz")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_respects_limit(self, store: ProteinStore) -> None:
        results = await store.search("Staphylococcus", limit=1)
        assert len(results) == 1
