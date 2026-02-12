from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.types import SMILES, InChIKey
    from ehrlich.shared.chemistry_port import ChemistryPort
    from ehrlich.shared.conformer import Conformer3D
    from ehrlich.shared.descriptors import MolecularDescriptors
    from ehrlich.shared.fingerprint import Fingerprint


class ChemistryService:
    def __init__(self, adapter: ChemistryPort | None = None) -> None:
        if adapter is None:
            from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter

            adapter = RDKitAdapter()
        self._adapter = adapter

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
