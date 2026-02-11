from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from ehrlich.simulation.application.simulation_service import _load_resistance_data

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def resistance_yaml(tmp_path: Path) -> Path:
    data = {
        "mutations": {
            "1VQQ": [
                {"mutation": "S403A", "risk": "HIGH", "mechanism": "Reduced binding"},
                {"mutation": "N146K", "risk": "MODERATE", "mechanism": "Altered access"},
            ],
            "2XCT": [
                {"mutation": "S84L", "risk": "HIGH", "mechanism": "Target alteration"},
            ],
        },
        "patterns": {
            "C1C(C(=O)N1)S": {"targets": ["1VQQ"]},
            "c1cc2c(cc1F)c(=O)": {"targets": ["2XCT"]},
        },
    }
    path = tmp_path / "resistance.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    return path


class TestLoadResistanceData:
    def test_loads_mutations(self, resistance_yaml: Path) -> None:
        mutations, patterns = _load_resistance_data(resistance_yaml)
        assert "1VQQ" in mutations
        assert len(mutations["1VQQ"]) == 2
        assert mutations["1VQQ"][0] == ("S403A", "HIGH", "Reduced binding")
        assert mutations["1VQQ"][1] == ("N146K", "MODERATE", "Altered access")

    def test_loads_patterns(self, resistance_yaml: Path) -> None:
        mutations, patterns = _load_resistance_data(resistance_yaml)
        assert "C1C(C(=O)N1)S" in patterns
        assert patterns["C1C(C(=O)N1)S"] == ["1VQQ"]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        mutations, patterns = _load_resistance_data(tmp_path / "nonexistent.yaml")
        assert mutations == {}
        assert patterns == {}

    def test_multiple_targets(self, resistance_yaml: Path) -> None:
        mutations, _ = _load_resistance_data(resistance_yaml)
        assert "2XCT" in mutations
        assert len(mutations["2XCT"]) == 1
        assert mutations["2XCT"][0][0] == "S84L"
