import json

import pytest

from ehrlich.literature import tools


class TestGetReference:
    @pytest.mark.asyncio
    async def test_known_key(self) -> None:
        result = json.loads(await tools.get_reference("halicin"))
        assert result["title"] == "A Deep Learning Approach to Antibiotic Discovery"
        assert result["year"] == 2020
        assert "citation" in result

    @pytest.mark.asyncio
    async def test_unknown_key(self) -> None:
        result = json.loads(await tools.get_reference("nonexistent_key"))
        assert "error" in result
        assert "available_keys" in result

    @pytest.mark.asyncio
    async def test_all_reference_keys(self) -> None:
        for key in ["halicin", "abaucin", "chemprop", "pkcsm", "who_bppl_2024", "amr_crisis"]:
            result = json.loads(await tools.get_reference(key))
            assert "title" in result, f"Key {key} not found"
            assert "error" not in result, f"Key {key} returned error"
