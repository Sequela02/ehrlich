"""Molecular-specific adapters for prediction ports.

These adapters use ChemistryPort (RDKit) to implement feature extraction,
scaffold-based splitting, and Butina clustering for molecular data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ehrlich.prediction.domain.ports import Clusterer, DataSplitter, FeatureExtractor

if TYPE_CHECKING:
    from ehrlich.shared.chemistry_port import ChemistryPort
    from ehrlich.shared.fingerprint import Fingerprint

logger = logging.getLogger(__name__)


class MolecularFeatureExtractor(FeatureExtractor):
    """Extracts Morgan fingerprint features from SMILES identifiers."""

    def __init__(self, rdkit: ChemistryPort) -> None:
        self._rdkit = rdkit

    def extract(self, identifiers: list[str]) -> tuple[list[list[float]], list[str]]:
        features: list[list[float]] = []
        valid: list[str] = []
        for smiles in identifiers:
            try:
                fp = self._rdkit.compute_fingerprint(smiles)  # type: ignore[arg-type]
                dense = self._fingerprint_to_dense(fp)
                features.append(dense)
                valid.append(smiles)
            except Exception:
                continue
        return features, valid

    @staticmethod
    def _fingerprint_to_dense(fp: Fingerprint) -> list[float]:
        dense = [0.0] * fp.n_bits
        for bit in fp.bits:
            dense[bit] = 1.0
        return dense


class ScaffoldSplitter(DataSplitter):
    """Scaffold-based train/test split for molecular data."""

    def __init__(self, rdkit: ChemistryPort) -> None:
        self._rdkit = rdkit

    def split(
        self,
        features: list[list[float]],
        labels: list[float],
        identifiers: list[str],
        test_size: float = 0.2,
    ) -> tuple[list[int], list[int]]:
        scaffolds = [self._safe_murcko_scaffold(s) for s in identifiers]

        unique_scaffolds = list(set(scaffolds))
        rng = np.random.RandomState(42)
        rng.shuffle(unique_scaffolds)

        n_test_scaffolds = max(1, int(len(unique_scaffolds) * test_size))
        test_scaffolds = set(unique_scaffolds[:n_test_scaffolds])

        train_idx = [i for i, s in enumerate(scaffolds) if s not in test_scaffolds]
        test_idx = [i for i, s in enumerate(scaffolds) if s in test_scaffolds]

        if not test_idx or not train_idx:
            all_idx = list(range(len(labels)))
            rng.shuffle(all_idx)
            split_point = int(len(all_idx) * (1 - test_size))
            train_idx = all_idx[:split_point]
            test_idx = all_idx[split_point:]

        return train_idx, test_idx

    def _safe_murcko_scaffold(self, smiles: str) -> str:
        try:
            return self._rdkit.murcko_scaffold(smiles)  # type: ignore[arg-type]
        except Exception:
            return "unknown"


class MolecularClusterer(Clusterer):
    """Butina clustering for molecular data using Tanimoto distance."""

    def __init__(self, rdkit: ChemistryPort) -> None:
        self._rdkit = rdkit

    def cluster(
        self,
        features: list[list[float]],
        identifiers: list[str],
        n_clusters: int,
    ) -> dict[int, list[str]]:
        fingerprints: list[Fingerprint] = []
        valid_ids: list[str] = []
        for smiles in identifiers:
            try:
                fp = self._rdkit.compute_fingerprint(smiles)  # type: ignore[arg-type]
                fingerprints.append(fp)
                valid_ids.append(smiles)
            except Exception:
                continue

        if not fingerprints:
            return {}

        clusters_indices = self._rdkit.butina_cluster(fingerprints, cutoff=0.35)

        result: dict[int, list[str]] = {}
        for cluster_id, indices in enumerate(clusters_indices):
            if cluster_id >= n_clusters:
                break
            result[cluster_id] = [valid_ids[i] for i in indices]
        return result
