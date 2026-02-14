"""Tests for impact-specific evaluation standards (CONEVAL, CREMAA)."""

from __future__ import annotations

from ehrlich.impact.domain.evaluation_standards import (
    CONEVAL_MIR_LEVELS,
    CREMAA_CRITERIA,
)


class TestCONEVALLevels:
    def test_all_levels_present(self) -> None:
        assert set(CONEVAL_MIR_LEVELS.keys()) == {"fin", "proposito", "componente", "actividad"}


class TestCREMAACriteria:
    def test_all_criteria_present(self) -> None:
        expected = {
            "claridad",
            "relevancia",
            "economia",
            "monitoreable",
            "adecuado",
            "aportacion_marginal",
        }
        assert set(CREMAA_CRITERIA.keys()) == expected
