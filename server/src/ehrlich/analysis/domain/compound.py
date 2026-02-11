from dataclasses import dataclass


@dataclass(frozen=True)
class CompoundSearchResult:
    """Compound search result from PubChem."""

    cid: int
    smiles: str
    iupac_name: str
    molecular_formula: str
    molecular_weight: float
    source: str = "pubchem"
