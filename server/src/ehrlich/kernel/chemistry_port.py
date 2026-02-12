from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.kernel.conformer import Conformer3D
    from ehrlich.kernel.descriptors import MolecularDescriptors
    from ehrlich.kernel.fingerprint import Fingerprint
    from ehrlich.kernel.types import SMILES, InChIKey


class ChemistryPort(ABC):
    @abstractmethod
    def validate_smiles(self, smiles: SMILES) -> bool: ...

    @abstractmethod
    def canonicalize(self, smiles: SMILES) -> SMILES: ...

    @abstractmethod
    def to_inchikey(self, smiles: SMILES) -> InChIKey: ...

    @abstractmethod
    def compute_descriptors(self, smiles: SMILES) -> MolecularDescriptors: ...

    @abstractmethod
    def compute_fingerprint(self, smiles: SMILES, fp_type: str = "morgan") -> Fingerprint: ...

    @abstractmethod
    def tanimoto_similarity(self, fp1: Fingerprint, fp2: Fingerprint) -> float: ...

    @abstractmethod
    def generate_conformer(self, smiles: SMILES) -> Conformer3D: ...

    @abstractmethod
    def substructure_match(self, smiles: SMILES, pattern: str) -> tuple[bool, tuple[int, ...]]: ...

    @abstractmethod
    def depict_2d(self, smiles: SMILES, width: int = 300, height: int = 200) -> str: ...

    @abstractmethod
    def murcko_scaffold(self, smiles: SMILES) -> str: ...

    @abstractmethod
    def butina_cluster(
        self, fingerprints: list[Fingerprint], cutoff: float = 0.35
    ) -> list[list[int]]: ...
