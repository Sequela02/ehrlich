"""Domain ports for the prediction bounded context.

These ABCs define the contracts for feature extraction, data splitting,
and clustering. Infrastructure adapters implement them for molecular
(RDKit-based) and generic (scipy-based) use cases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class FeatureExtractor(ABC):
    @abstractmethod
    def extract(self, identifiers: list[str]) -> tuple[list[list[float]], list[str]]:
        """Extract feature vectors from identifiers.

        Returns (feature_vectors, valid_identifiers). Drops invalid identifiers.
        """
        ...


class DataSplitter(ABC):
    @abstractmethod
    def split(
        self,
        features: list[list[float]],
        labels: list[float],
        identifiers: list[str],
        test_size: float = 0.2,
    ) -> tuple[list[int], list[int]]:
        """Split data into train/test sets.

        Returns (train_indices, test_indices).
        """
        ...


class Clusterer(ABC):
    @abstractmethod
    def cluster(
        self,
        features: list[list[float]],
        identifiers: list[str],
        n_clusters: int,
    ) -> dict[int, list[str]]:
        """Cluster data points.

        Returns {cluster_id: [identifiers]}.
        """
        ...
