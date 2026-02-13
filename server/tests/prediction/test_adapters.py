"""Tests for prediction infrastructure adapters (real implementations, no mocks)."""

from __future__ import annotations

import numpy as np

from ehrlich.chemistry.infrastructure.rdkit_adapter import RDKitAdapter
from ehrlich.prediction.infrastructure.generic_adapters import (
    DistanceClusterer,
    RandomSplitter,
)
from ehrlich.prediction.infrastructure.molecular_adapters import (
    MolecularClusterer,
    MolecularFeatureExtractor,
    ScaffoldSplitter,
)

# -- Molecular adapters -------------------------------------------------------


class TestMolecularFeatureExtractor:
    def test_extracts_features_from_valid_smiles(self) -> None:
        ext = MolecularFeatureExtractor(RDKitAdapter())
        features, valid = ext.extract(["c1ccccc1", "CCO", "c1ccncc1"])
        assert len(features) == 3
        assert len(valid) == 3
        assert len(features[0]) == 2048  # Morgan fingerprint default

    def test_drops_invalid_smiles(self) -> None:
        ext = MolecularFeatureExtractor(RDKitAdapter())
        features, valid = ext.extract(["c1ccccc1", "INVALID_SMILES_XYZ", "CCO"])
        assert len(features) == 2
        assert valid == ["c1ccccc1", "CCO"]

    def test_empty_input_returns_empty(self) -> None:
        ext = MolecularFeatureExtractor(RDKitAdapter())
        features, valid = ext.extract([])
        assert features == []
        assert valid == []


class TestScaffoldSplitter:
    def test_split_preserves_total(self) -> None:
        splitter = ScaffoldSplitter(RDKitAdapter())
        smiles = [
            "c1ccc(cc1)O",
            "c1ccc(cc1)N",
            "CC(=O)Oc1ccccc1C(=O)O",
            "c1ccncc1",
            "c1ccc2[nH]ccc2c1",
            "OC(=O)c1ccccc1",
            "c1ccc2c(c1)cccc2",
            "CCCCCC",
            "CCCCCCCCCC",
            "C1CCCCC1",
            "CC(C)CC",
            "CCOC(=O)CC",
            "CCC(=O)C",
            "CCCCCCCCC",
        ]
        features = [[float(i)] * 10 for i in range(len(smiles))]
        labels = [1.0] * 7 + [0.0] * 7
        train_idx, test_idx = splitter.split(features, labels, smiles)
        assert len(train_idx) + len(test_idx) == len(smiles)
        assert len(train_idx) > 0
        assert len(test_idx) > 0

    def test_single_scaffold_fallback(self) -> None:
        splitter = ScaffoldSplitter(RDKitAdapter())
        smiles = ["CCCCCC"] * 14  # All same scaffold
        features = [[float(i)] * 10 for i in range(14)]
        labels = [1.0] * 7 + [0.0] * 7
        train_idx, test_idx = splitter.split(features, labels, smiles)
        assert len(train_idx) + len(test_idx) == 14
        assert len(test_idx) > 0


class TestMolecularClusterer:
    def test_returns_valid_clusters(self) -> None:
        clusterer = MolecularClusterer(RDKitAdapter())
        smiles = [
            "c1ccc(cc1)O",
            "c1ccc(cc1)N",
            "CC(=O)Oc1ccccc1C(=O)O",
            "c1ccncc1",
            "CCCCCC",
            "CCCCCCCCCC",
            "C1CCCCC1",
        ]
        features = [[0.0]] * len(smiles)  # Not used by MolecularClusterer
        clusters = clusterer.cluster(features, smiles, n_clusters=20)
        assert len(clusters) > 0
        all_items = [s for group in clusters.values() for s in group]
        assert len(all_items) == len(smiles)

    def test_empty_input(self) -> None:
        clusterer = MolecularClusterer(RDKitAdapter())
        clusters = clusterer.cluster([], [], n_clusters=5)
        assert clusters == {}


# -- Generic adapters ----------------------------------------------------------


class TestRandomSplitter:
    def test_split_preserves_total(self) -> None:
        splitter = RandomSplitter()
        features = [[float(i)] * 4 for i in range(20)]
        labels = [1.0] * 10 + [0.0] * 10
        ids = [f"s_{i}" for i in range(20)]
        train_idx, test_idx = splitter.split(features, labels, ids)
        assert len(train_idx) + len(test_idx) == 20
        assert len(train_idx) == 16  # 80% of 20
        assert len(test_idx) == 4

    def test_deterministic(self) -> None:
        splitter = RandomSplitter()
        features = [[float(i)] * 4 for i in range(20)]
        labels = [1.0] * 10 + [0.0] * 10
        ids = [f"s_{i}" for i in range(20)]
        t1, te1 = splitter.split(features, labels, ids)
        t2, te2 = splitter.split(features, labels, ids)
        assert t1 == t2
        assert te1 == te2


class TestDistanceClusterer:
    def test_returns_correct_number_of_clusters(self) -> None:
        clusterer = DistanceClusterer()
        rng = np.random.RandomState(42)
        features = rng.rand(20, 4).tolist()
        ids = [f"s_{i}" for i in range(20)]
        clusters = clusterer.cluster(features, ids, n_clusters=3)
        assert len(clusters) == 3
        all_items = [s for group in clusters.values() for s in group]
        assert len(all_items) == 20

    def test_empty_input(self) -> None:
        clusterer = DistanceClusterer()
        clusters = clusterer.cluster([], [], n_clusters=5)
        assert clusters == {}

    def test_fewer_samples_than_clusters(self) -> None:
        clusterer = DistanceClusterer()
        features = [[1.0, 2.0], [3.0, 4.0]]
        ids = ["a", "b"]
        clusters = clusterer.cluster(features, ids, n_clusters=5)
        assert len(clusters) == 2
        assert clusters[0] == ["a"]
        assert clusters[1] == ["b"]
