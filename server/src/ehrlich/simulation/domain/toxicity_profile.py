from dataclasses import dataclass


@dataclass(frozen=True)
class ToxicityProfile:
    """Environmental toxicity profile from EPA CompTox."""

    dtxsid: str
    name: str
    casrn: str
    molecular_weight: float
    oral_rat_ld50: float | None
    lc50_fish: float | None
    bioconcentration_factor: float | None
    developmental_toxicity: bool | None
    mutagenicity: bool | None
    source: str = "epa_comptox"
