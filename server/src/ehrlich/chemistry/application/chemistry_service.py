from ehrlich.chemistry.domain.conformer import Conformer3D
from ehrlich.chemistry.domain.descriptors import MolecularDescriptors
from ehrlich.kernel.types import SMILES


class ChemistryService:
    async def generate_conformer(self, smiles: SMILES) -> Conformer3D:
        raise NotImplementedError

    async def compute_descriptors(self, smiles: SMILES) -> MolecularDescriptors:
        raise NotImplementedError

    async def match_substructure(self, smiles: SMILES, pattern: str) -> bool:
        raise NotImplementedError
