from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProteinAnnotation:
    accession: str
    name: str
    organism: str
    function: str
    disease_associations: list[str] = field(default_factory=list)
    go_terms: list[str] = field(default_factory=list)
    pdb_cross_refs: list[str] = field(default_factory=list)
    pathway: str = ""
