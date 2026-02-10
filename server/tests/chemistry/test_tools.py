import json

import pytest

from ehrlich.chemistry import tools


class TestGenerare3D:
    @pytest.mark.asyncio
    async def test_valid_smiles(self) -> None:
        result = json.loads(await tools.generate_3d("CCO"))
        assert "mol_block" in result
        assert result["num_atoms"] > 0
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_invalid_smiles(self) -> None:
        result = json.loads(await tools.generate_3d("INVALID!!!"))
        assert "error" in result


class TestSubstructureMatch:
    @pytest.mark.asyncio
    async def test_match_found(self) -> None:
        result = json.loads(await tools.substructure_match("c1ccccc1O", "c1ccccc1"))
        assert result["matched"] is True
        assert len(result["matching_atoms"]) == 6

    @pytest.mark.asyncio
    async def test_no_match(self) -> None:
        result = json.loads(await tools.substructure_match("CCO", "c1ccccc1"))
        assert result["matched"] is False


class TestComputeDescriptors:
    @pytest.mark.asyncio
    async def test_valid(self) -> None:
        result = json.loads(await tools.compute_descriptors("CCO"))
        assert "molecular_weight" in result
        assert result["passes_lipinski"] is True

    @pytest.mark.asyncio
    async def test_invalid(self) -> None:
        result = json.loads(await tools.compute_descriptors("INVALID!!!"))
        assert "error" in result


class TestValidateSmiles:
    @pytest.mark.asyncio
    async def test_valid(self) -> None:
        result = json.loads(await tools.validate_smiles("CCO"))
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_invalid(self) -> None:
        result = json.loads(await tools.validate_smiles("INVALID!!!"))
        assert result["valid"] is False


class TestTanimotoSimilarity:
    @pytest.mark.asyncio
    async def test_identical(self) -> None:
        result = json.loads(await tools.tanimoto_similarity("CCO", "CCO"))
        assert result["similarity"] == 1.0

    @pytest.mark.asyncio
    async def test_different(self) -> None:
        result = json.loads(await tools.tanimoto_similarity("CCO", "c1ccccc1"))
        assert 0.0 <= result["similarity"] < 1.0


class TestModifyMolecule:
    @pytest.mark.asyncio
    async def test_not_implemented(self) -> None:
        result = json.loads(await tools.modify_molecule("CCO", "add_methyl"))
        assert result["status"] == "not_implemented"
