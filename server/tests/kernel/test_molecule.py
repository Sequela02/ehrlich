import pytest

from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.molecule import Molecule
from ehrlich.kernel.types import SMILES


class TestMolecule:
    def test_valid_smiles(self, aspirin_smiles: SMILES) -> None:
        mol = Molecule(smiles=aspirin_smiles)
        assert mol.smiles == aspirin_smiles

    def test_empty_smiles_raises(self) -> None:
        with pytest.raises(InvalidSMILESError):
            Molecule(smiles=SMILES(""))

    def test_whitespace_smiles_raises(self) -> None:
        with pytest.raises(InvalidSMILESError):
            Molecule(smiles=SMILES("   "))

    def test_invalid_characters_raises(self) -> None:
        with pytest.raises(InvalidSMILESError):
            Molecule(smiles=SMILES("invalid smiles!!!"))

    def test_frozen(self, aspirin_smiles: SMILES) -> None:
        mol = Molecule(smiles=aspirin_smiles)
        with pytest.raises(AttributeError):
            mol.smiles = SMILES("C")  # type: ignore[misc]
