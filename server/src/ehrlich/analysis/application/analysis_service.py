from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from scipy import stats

from ehrlich.analysis.domain.enrichment import EnrichmentResult

if TYPE_CHECKING:
    from ehrlich.analysis.domain.compound import CompoundSearchResult
    from ehrlich.analysis.domain.dataset import Dataset
    from ehrlich.analysis.domain.repository import CompoundSearchRepository, DatasetRepository
    from ehrlich.kernel.chemistry_port import ChemistryPort

logger = logging.getLogger(__name__)

_KNOWN_SUBSTRUCTURES: dict[str, tuple[str, str]] = {
    "beta_lactam": ("[C@@H]1([C@@H](N1)C(=O)O)S", "Beta-lactam ring (penicillins)"),
    "fluoroquinolone": ("c1cc2c(cc1F)c(=O)c(cn2)C(=O)O", "Fluoroquinolone core"),
    "sulfonamide": ("NS(=O)(=O)c1ccc(N)cc1", "Sulfonamide group"),
    "benzene": ("c1ccccc1", "Benzene ring"),
    "phenol": ("c1ccc(cc1)O", "Phenol group"),
    "amine": ("[NX3;H2,H1,H0]", "Primary/secondary/tertiary amine"),
    "carboxylic_acid": ("[CX3](=O)[OX2H1]", "Carboxylic acid"),
    "amide": ("[CX3](=[OX1])[NX3]", "Amide bond"),
    "hydroxyl": ("[OX2H]", "Hydroxyl group"),
    "nitro": ("[NX3](=O)=O", "Nitro group"),
}


class AnalysisService:
    def __init__(
        self,
        repository: DatasetRepository,
        compound_repo: CompoundSearchRepository | None = None,
        chemistry: ChemistryPort | None = None,
    ) -> None:
        self._repository = repository
        self._compound_repo = compound_repo
        if chemistry is None:
            from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter

            chemistry = RDKitAdapter()
        self._adapter = chemistry

    async def search_compounds(self, query: str, limit: int = 10) -> list[CompoundSearchResult]:
        if self._compound_repo is None:
            return []
        return await self._compound_repo.search(query, limit)

    async def search_by_similarity(
        self, smiles: str, threshold: float = 0.8, limit: int = 10
    ) -> list[CompoundSearchResult]:
        if self._compound_repo is None:
            return []
        return await self._compound_repo.search_by_similarity(smiles, threshold, limit)

    async def explore(self, target: str, threshold: float = 1.0) -> Dataset:
        return await self._repository.load(target, threshold)

    async def search_bioactivity(
        self,
        target: str,
        assay_types: list[str] | None = None,
        threshold: float = 1.0,
    ) -> Dataset:
        return await self._repository.search_bioactivity(target, assay_types, threshold)

    async def analyze_substructures(self, dataset: Dataset) -> list[EnrichmentResult]:
        if dataset.size == 0:
            return []
        results: list[EnrichmentResult] = []
        active_smiles = [
            dataset.smiles_list[i] for i in range(dataset.size) if dataset.activities[i] >= 0.5
        ]
        inactive_smiles = [
            dataset.smiles_list[i] for i in range(dataset.size) if dataset.activities[i] < 0.5
        ]
        if not active_smiles or not inactive_smiles:
            return []
        for name, (pattern, desc) in _KNOWN_SUBSTRUCTURES.items():
            active_hits = sum(
                1 for s in active_smiles if self._adapter.substructure_match(s, pattern)[0]
            )
            inactive_hits = sum(
                1 for s in inactive_smiles if self._adapter.substructure_match(s, pattern)[0]
            )
            table = np.array(
                [
                    [active_hits, len(active_smiles) - active_hits],
                    [inactive_hits, len(inactive_smiles) - inactive_hits],
                ]
            )
            if table.min() < 0 or table.sum() == 0:
                continue
            if active_hits + inactive_hits == 0:
                continue
            try:
                chi2, p_value, _, _ = stats.chi2_contingency(table, correction=True)
            except ValueError:
                continue
            a, b, c, d = table.ravel()
            odds_ratio = (a * d) / (b * c) if (b * c) > 0 else float("inf")
            results.append(
                EnrichmentResult(
                    substructure=name,
                    p_value=p_value,
                    odds_ratio=odds_ratio,
                    active_count=active_hits,
                    total_count=active_hits + inactive_hits,
                    description=desc,
                )
            )
        results.sort(key=lambda r: r.p_value)
        return results

    async def compute_properties(self, dataset: Dataset) -> dict[str, object]:
        if dataset.size == 0:
            return {"error": "Empty dataset"}
        active_descs = []
        inactive_descs = []
        for i, smiles in enumerate(dataset.smiles_list):
            try:
                desc = self._adapter.compute_descriptors(smiles)
            except Exception:
                continue
            if dataset.activities[i] >= 0.5:
                active_descs.append(desc)
            else:
                inactive_descs.append(desc)
        props = ["molecular_weight", "logp", "tpsa", "hbd", "hba", "rotatable_bonds", "qed"]
        summary: dict[str, object] = {
            "total": dataset.size,
            "active_count": len(active_descs),
            "inactive_count": len(inactive_descs),
        }
        for prop in props:
            active_vals = [getattr(d, prop) for d in active_descs] if active_descs else []
            inactive_vals = [getattr(d, prop) for d in inactive_descs] if inactive_descs else []
            summary[prop] = {
                "active_mean": float(np.mean(active_vals)) if active_vals else 0.0,
                "active_std": float(np.std(active_vals)) if active_vals else 0.0,
                "inactive_mean": float(np.mean(inactive_vals)) if inactive_vals else 0.0,
                "inactive_std": float(np.std(inactive_vals)) if inactive_vals else 0.0,
            }
        return summary
