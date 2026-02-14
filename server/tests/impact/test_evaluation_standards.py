"""Tests for impact evaluation evidence standards."""

from __future__ import annotations

from ehrlich.impact.domain.entities import ThreatToValidity
from ehrlich.impact.domain.evaluation_standards import (
    CONEVAL_MIR_LEVELS,
    CREMAA_CRITERIA,
    WWC_TIERS,
    classify_evidence_tier,
)


class TestWWCTiers:
    def test_all_tiers_present(self) -> None:
        assert set(WWC_TIERS.keys()) == {"strong", "moderate", "promising", "rationale"}

    def test_tiers_have_descriptions(self) -> None:
        for tier, desc in WWC_TIERS.items():
            assert isinstance(desc, str)
            assert len(desc) > 10, f"Tier {tier} has short description"


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


class TestClassifyEvidenceTier:
    def test_rct_no_threats(self) -> None:
        assert classify_evidence_tier("rct", []) == "strong"

    def test_rct_with_severe_threat(self) -> None:
        threats = [
            ThreatToValidity(
                type="attrition",
                severity="high",
                description="30% dropout",
                mitigation="ITT analysis",
            )
        ]
        assert classify_evidence_tier("rct", threats) == "moderate"

    def test_rct_with_two_severe_threats(self) -> None:
        threats = [
            ThreatToValidity(
                type="attrition", severity="high", description="30% dropout", mitigation="ITT"
            ),
            ThreatToValidity(
                type="contamination", severity="high", description="Cross-group", mitigation="None"
            ),
        ]
        assert classify_evidence_tier("rct", threats) == "moderate"

    def test_did_no_threats(self) -> None:
        assert classify_evidence_tier("did", []) == "moderate"

    def test_did_alias(self) -> None:
        assert classify_evidence_tier("difference_in_differences", []) == "moderate"

    def test_psm_no_threats(self) -> None:
        assert classify_evidence_tier("psm", []) == "moderate"

    def test_psm_with_severe_threats(self) -> None:
        threats = [
            ThreatToValidity(
                type="selection", severity="high", description="Unobserved", mitigation="None"
            ),
            ThreatToValidity(
                type="specification", severity="high", description="Wrong model", mitigation="None"
            ),
        ]
        assert classify_evidence_tier("psm", threats) == "promising"

    def test_rdd_no_threats(self) -> None:
        assert classify_evidence_tier("rdd", []) == "moderate"

    def test_synthetic_control(self) -> None:
        assert classify_evidence_tier("synthetic_control", []) == "moderate"

    def test_iv_no_threats(self) -> None:
        assert classify_evidence_tier("iv", []) == "promising"

    def test_iv_with_severe_threat(self) -> None:
        threats = [
            ThreatToValidity(
                type="weak_instrument", severity="high", description="F<10", mitigation="None"
            )
        ]
        assert classify_evidence_tier("iv", threats) == "rationale"

    def test_fixed_effects(self) -> None:
        assert classify_evidence_tier("fixed_effects", []) == "promising"

    def test_descriptive_method(self) -> None:
        assert classify_evidence_tier("descriptive", []) == "rationale"

    def test_unknown_method(self) -> None:
        assert classify_evidence_tier("survey", []) == "rationale"

    def test_low_severity_threats_not_counted(self) -> None:
        threats = [
            ThreatToValidity(
                type="attrition", severity="low", description="5% dropout", mitigation="Robust SE"
            )
        ]
        assert classify_evidence_tier("rct", threats) == "strong"
