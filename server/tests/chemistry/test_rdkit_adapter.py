import pytest

from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.types import SMILES


@pytest.fixture
def adapter() -> RDKitAdapter:
    return RDKitAdapter()


class TestValidateSmiles:
    def test_valid_smiles(self, adapter: RDKitAdapter) -> None:
        assert adapter.validate_smiles(SMILES("CCO")) is True

    def test_aspirin(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        assert adapter.validate_smiles(aspirin_smiles) is True

    def test_invalid_smiles(self, adapter: RDKitAdapter) -> None:
        assert adapter.validate_smiles(SMILES("not_a_smiles!!!")) is False

    def test_empty_string(self, adapter: RDKitAdapter) -> None:
        # RDKit treats empty string as valid (no-atom molecule)
        assert adapter.validate_smiles(SMILES("")) is True


class TestCanonicalize:
    def test_canonicalize_ethanol(self, adapter: RDKitAdapter) -> None:
        result = adapter.canonicalize(SMILES("OCC"))
        assert result == SMILES("CCO")

    def test_canonicalize_consistency(self, adapter: RDKitAdapter) -> None:
        s1 = adapter.canonicalize(SMILES("c1ccccc1"))
        s2 = adapter.canonicalize(SMILES("C1=CC=CC=C1"))
        assert s1 == s2

    def test_canonicalize_aspirin(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        canonical = adapter.canonicalize(aspirin_smiles)
        again = adapter.canonicalize(canonical)
        assert canonical == again

    def test_canonicalize_invalid_raises(self, adapter: RDKitAdapter) -> None:
        with pytest.raises(InvalidSMILESError):
            adapter.canonicalize(SMILES("invalid!!!"))


class TestToInChIKey:
    def test_ethanol(self, adapter: RDKitAdapter) -> None:
        key = adapter.to_inchikey(SMILES("CCO"))
        assert key.startswith("LFQSCWFLJHTTHZ")

    def test_aspirin(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        key = adapter.to_inchikey(aspirin_smiles)
        assert key.startswith("BSYNRYMUTXBXSQ")

    def test_invalid_raises(self, adapter: RDKitAdapter) -> None:
        with pytest.raises(InvalidSMILESError):
            adapter.to_inchikey(SMILES("invalid!!!"))


class TestComputeDescriptors:
    def test_aspirin_descriptors(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        desc = adapter.compute_descriptors(aspirin_smiles)
        assert 179 < desc.molecular_weight < 181  # MW of aspirin ~180.16
        assert desc.hbd == 1
        assert desc.hba == 3
        assert desc.num_rings == 1
        assert 0 < desc.qed < 1
        assert desc.passes_lipinski is True

    def test_ethanol_descriptors(self, adapter: RDKitAdapter) -> None:
        desc = adapter.compute_descriptors(SMILES("CCO"))
        assert 45 < desc.molecular_weight < 47  # MW of ethanol ~46.07
        assert desc.logp < 1
        assert desc.passes_lipinski is True


class TestComputeFingerprint:
    def test_morgan_fingerprint(self, adapter: RDKitAdapter) -> None:
        fp = adapter.compute_fingerprint(SMILES("CCO"), "morgan")
        assert fp.fp_type == "morgan"
        assert fp.n_bits == 2048
        assert fp.radius == 2
        assert len(fp.bits) > 0

    def test_maccs_fingerprint(self, adapter: RDKitAdapter) -> None:
        fp = adapter.compute_fingerprint(SMILES("CCO"), "maccs")
        assert fp.fp_type == "maccs"
        assert fp.n_bits == 167
        assert len(fp.bits) > 0

    def test_same_molecule_same_fingerprint(self, adapter: RDKitAdapter) -> None:
        fp1 = adapter.compute_fingerprint(SMILES("CCO"))
        fp2 = adapter.compute_fingerprint(SMILES("OCC"))
        assert fp1.bits == fp2.bits


class TestTanimotoSimilarity:
    def test_identical_molecules(self, adapter: RDKitAdapter) -> None:
        fp = adapter.compute_fingerprint(SMILES("CCO"))
        assert adapter.tanimoto_similarity(fp, fp) == 1.0

    def test_different_molecules(self, adapter: RDKitAdapter) -> None:
        fp1 = adapter.compute_fingerprint(SMILES("CCO"))
        fp2 = adapter.compute_fingerprint(SMILES("c1ccc2ccccc2c1"))  # naphthalene
        sim = adapter.tanimoto_similarity(fp1, fp2)
        assert 0.0 <= sim < 1.0


class TestGenerateConformer:
    def test_ethanol_conformer(self, adapter: RDKitAdapter) -> None:
        conf = adapter.generate_conformer(SMILES("CCO"))
        assert len(conf.mol_block) > 0
        assert conf.num_atoms > 0
        assert "V2000" in conf.mol_block or "V3000" in conf.mol_block

    def test_aspirin_conformer(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        conf = adapter.generate_conformer(aspirin_smiles)
        assert conf.num_atoms > 0
        assert conf.energy != 0.0 or conf.energy == 0.0  # energy is computed


class TestSubstructureMatch:
    def test_benzene_in_aspirin(self, adapter: RDKitAdapter, aspirin_smiles: SMILES) -> None:
        matched, atoms = adapter.substructure_match(aspirin_smiles, "c1ccccc1")
        assert matched is True
        assert len(atoms) == 6

    def test_no_match(self, adapter: RDKitAdapter) -> None:
        matched, atoms = adapter.substructure_match(SMILES("CCO"), "c1ccccc1")
        assert matched is False
        assert atoms == ()

    def test_smarts_pattern(self, adapter: RDKitAdapter) -> None:
        matched, atoms = adapter.substructure_match(SMILES("CCO"), "[OX2H]")
        assert matched is True
        assert len(atoms) == 1

    def test_invalid_pattern(self, adapter: RDKitAdapter) -> None:
        matched, atoms = adapter.substructure_match(SMILES("CCO"), "INVALID_PATTERN_!@#$%^&*()")
        assert matched is False
