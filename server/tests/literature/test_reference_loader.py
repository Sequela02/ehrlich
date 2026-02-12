from pathlib import Path

from ehrlich.literature.infrastructure.reference_loader import load_core_references


class TestLoadCoreReferences:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_core_references(tmp_path / "nonexistent.json")
        assert len(result.papers) == 0

    def test_default_loads_successfully(self) -> None:
        result = load_core_references()
        assert len(result.papers) > 0
        assert result.find_by_key("halicin") is not None
