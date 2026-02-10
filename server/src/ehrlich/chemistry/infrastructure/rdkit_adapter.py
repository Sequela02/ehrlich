from ehrlich.chemistry.domain.conformer import Conformer3D
from ehrlich.chemistry.domain.descriptors import MolecularDescriptors
from ehrlich.chemistry.domain.fingerprint import Fingerprint
from ehrlich.kernel.types import SMILES


class RDKitAdapter:
    def validate_smiles(self, smiles: SMILES) -> bool:
        raise NotImplementedError

    def canonicalize(self, smiles: SMILES) -> SMILES:
        raise NotImplementedError

    def generate_conformer(self, smiles: SMILES) -> Conformer3D:
        raise NotImplementedError

    def compute_descriptors(self, smiles: SMILES) -> MolecularDescriptors:
        raise NotImplementedError

    def compute_fingerprint(self, smiles: SMILES, fp_type: str = "morgan") -> Fingerprint:
        raise NotImplementedError

    def substructure_match(self, smiles: SMILES, pattern: str) -> bool:
        raise NotImplementedError
