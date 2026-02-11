from ehrlich.chemistry.domain.conformer import Conformer3D
from ehrlich.chemistry.domain.descriptors import MolecularDescriptors
from ehrlich.chemistry.domain.fingerprint import Fingerprint
from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.kernel.types import SMILES, InChIKey


class ChemistryService:
    def __init__(self, adapter: RDKitAdapter | None = None) -> None:
        self._adapter = adapter or RDKitAdapter()

    def validate_smiles(self, smiles: SMILES) -> bool:
        return self._adapter.validate_smiles(smiles)

    def canonicalize(self, smiles: SMILES) -> SMILES:
        return self._adapter.canonicalize(smiles)

    def to_inchikey(self, smiles: SMILES) -> InChIKey:
        return self._adapter.to_inchikey(smiles)

    def compute_descriptors(self, smiles: SMILES) -> MolecularDescriptors:
        return self._adapter.compute_descriptors(smiles)

    def compute_fingerprint(self, smiles: SMILES, fp_type: str = "morgan") -> Fingerprint:
        return self._adapter.compute_fingerprint(smiles, fp_type)

    def tanimoto_similarity(self, fp1: Fingerprint, fp2: Fingerprint) -> float:
        return self._adapter.tanimoto_similarity(fp1, fp2)

    def generate_conformer(self, smiles: SMILES) -> Conformer3D:
        return self._adapter.generate_conformer(smiles)

    def depict_2d(self, smiles: SMILES, width: int = 300, height: int = 200) -> str:
        return self._adapter.depict_2d(smiles, width, height)

    def substructure_match(self, smiles: SMILES, pattern: str) -> tuple[bool, tuple[int, ...]]:
        return self._adapter.substructure_match(smiles, pattern)
