"""Generic (domain-agnostic) adapters for prediction ports.

These adapters work with any numeric feature matrix -- no molecular
dependencies. Used by training science, nutrition science, and any
future domain that needs ML capabilities.
"""

from __future__ import annotations

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from ehrlich.prediction.domain.ports import Clusterer, DataSplitter


class RandomSplitter(DataSplitter):
    """Random shuffle train/test split with fixed seed."""

    def split(
        self,
        features: list[list[float]],
        labels: list[float],
        identifiers: list[str],
        test_size: float = 0.2,
    ) -> tuple[list[int], list[int]]:
        rng = np.random.RandomState(42)
        indices = list(range(len(labels)))
        rng.shuffle(indices)
        split_point = int(len(indices) * (1 - test_size))
        return indices[:split_point], indices[split_point:]


class DistanceClusterer(Clusterer):
    """Hierarchical clustering using Ward linkage (scipy)."""

    def cluster(
        self,
        features: list[list[float]],
        identifiers: list[str],
        n_clusters: int,
    ) -> dict[int, list[str]]:
        if not features:
            return {}

        n_samples = len(features)
        if n_samples <= n_clusters:
            return {i: [identifiers[i]] for i in range(n_samples)}

        x = np.array(features, dtype=np.float64)
        z = linkage(x, method="ward")
        labels = fcluster(z, t=n_clusters, criterion="maxclust")

        result: dict[int, list[str]] = {}
        for idx, cluster_id in enumerate(labels):
            cid = int(cluster_id) - 1  # fcluster is 1-indexed
            result.setdefault(cid, []).append(identifiers[idx])
        return result
