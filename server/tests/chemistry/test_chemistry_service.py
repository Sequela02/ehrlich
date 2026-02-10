import pytest

from ehrlich.chemistry.application.chemistry_service import ChemistryService
from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.types import SMILES


@pytest.fixture
def service() -> ChemistryService:
    return ChemistryService()


class TestChemistryService:
    def test_validate_valid(self, service: ChemistryService) -> None:
        assert service.validate_smiles(SMILES("CCO")) is True

    def test_validate_invalid(self, service: ChemistryService) -> None:
        assert service.validate_smiles(SMILES("INVALID!!!")) is False

    def test_canonicalize(self, service: ChemistryService) -> None:
        assert service.canonicalize(SMILES("OCC")) == SMILES("CCO")

    def test_to_inchikey(self, service: ChemistryService) -> None:
        key = service.to_inchikey(SMILES("CCO"))
        assert len(key) == 27  # InChIKey length

    def test_compute_descriptors(self, service: ChemistryService) -> None:
        desc = service.compute_descriptors(SMILES("CCO"))
        assert desc.molecular_weight > 0
        assert desc.passes_lipinski is True

    def test_fingerprint_and_similarity(self, service: ChemistryService) -> None:
        fp1 = service.compute_fingerprint(SMILES("CCO"))
        fp2 = service.compute_fingerprint(SMILES("CCO"))
        assert service.tanimoto_similarity(fp1, fp2) == 1.0

    def test_generate_conformer(self, service: ChemistryService) -> None:
        conf = service.generate_conformer(SMILES("CCO"))
        assert conf.num_atoms > 0
        assert len(conf.mol_block) > 0

    def test_substructure_match(self, service: ChemistryService) -> None:
        matched, atoms = service.substructure_match(SMILES("c1ccccc1O"), "c1ccccc1")
        assert matched is True
        assert len(atoms) == 6

    def test_invalid_smiles_raises(self, service: ChemistryService) -> None:
        with pytest.raises(InvalidSMILESError):
            service.canonicalize(SMILES("INVALID!!!"))
