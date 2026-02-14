from __future__ import annotations

import pytest

from ehrlich.investigation.application.tree_manager import TreeManager
from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus
from ehrlich.investigation.domain.investigation import Investigation


def _make_hypothesis(
    *,
    statement: str = "Test hypothesis",
    status: HypothesisStatus = HypothesisStatus.PROPOSED,
    depth: int = 0,
    branch_score: float = 0.0,
    parent_id: str = "",
    prior_confidence: float = 0.5,
    certainty_of_evidence: str = "",
) -> Hypothesis:
    h = Hypothesis(
        statement=statement,
        rationale="Test rationale",
        status=status,
        depth=depth,
        parent_id=parent_id,
        prior_confidence=prior_confidence,
        certainty_of_evidence=certainty_of_evidence,
    )
    h.branch_score = branch_score
    return h


class TestSelectNext:
    def test_returns_highest_branch_score(self) -> None:
        tm = TreeManager()
        h1 = _make_hypothesis(statement="Low score", branch_score=0.3)
        h2 = _make_hypothesis(statement="High score", branch_score=0.9)
        h3 = _make_hypothesis(statement="Mid score", branch_score=0.6)
        h4 = _make_hypothesis(statement="Also mid", branch_score=0.5)

        result = tm.select_next([h1, h2, h3, h4])

        assert len(result) == 2
        assert result[0] is h2
        assert result[1] is h3

    def test_respects_max_depth(self) -> None:
        tm = TreeManager(max_depth=2)
        h1 = _make_hypothesis(statement="Depth 0", depth=0, branch_score=0.5)
        h2 = _make_hypothesis(statement="Depth 2", depth=2, branch_score=0.9)
        h3 = _make_hypothesis(statement="Depth 3", depth=3, branch_score=1.0)

        result = tm.select_next([h1, h2, h3])

        assert len(result) == 1
        assert result[0] is h1

    def test_only_selects_proposed(self) -> None:
        tm = TreeManager()
        h1 = _make_hypothesis(status=HypothesisStatus.SUPPORTED, branch_score=0.9)
        h2 = _make_hypothesis(status=HypothesisStatus.REFUTED, branch_score=0.8)
        h3 = _make_hypothesis(status=HypothesisStatus.PROPOSED, branch_score=0.3)

        result = tm.select_next([h1, h2, h3])

        assert len(result) == 1
        assert result[0] is h3

    def test_returns_empty_when_no_candidates(self) -> None:
        tm = TreeManager()
        h1 = _make_hypothesis(status=HypothesisStatus.SUPPORTED)

        result = tm.select_next([h1])

        assert result == []

    def test_depth_tiebreak(self) -> None:
        """Shallowest depth wins when scores are equal."""
        tm = TreeManager()
        h1 = _make_hypothesis(statement="Deep", depth=2, branch_score=0.5)
        h2 = _make_hypothesis(statement="Shallow", depth=0, branch_score=0.5)

        result = tm.select_next([h1, h2])

        assert len(result) == 2
        assert result[0] is h2
        assert result[1] is h1

    def test_returns_max_two(self) -> None:
        tm = TreeManager()
        hypotheses = [
            _make_hypothesis(statement=f"H{i}", branch_score=float(i) / 10) for i in range(5)
        ]

        result = tm.select_next(hypotheses)

        assert len(result) == 2


class TestComputeBranchScore:
    def test_base_from_prior_confidence(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(prior_confidence=0.8, depth=0)

        score = tm.compute_branch_score(h, inv)

        assert score == 0.8

    def test_default_confidence_when_zero(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(prior_confidence=0.0, depth=0)

        score = tm.compute_branch_score(h, inv)

        assert score == 0.5

    def test_depth_discount(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h0 = _make_hypothesis(prior_confidence=1.0, depth=0)
        h1 = _make_hypothesis(prior_confidence=1.0, depth=1)
        h2 = _make_hypothesis(prior_confidence=1.0, depth=2)

        s0 = tm.compute_branch_score(h0, inv)
        s1 = tm.compute_branch_score(h1, inv)
        s2 = tm.compute_branch_score(h2, inv)

        assert s0 > s1 > s2
        # depth=0: 1.0 / (1 + 0) = 1.0
        # depth=1: 1.0 / (1 + 0.2) = 0.8333
        # depth=2: 1.0 / (1 + 0.4) = 0.7143
        assert s0 == 1.0
        assert s1 == pytest.approx(0.8333, abs=0.001)
        assert s2 == pytest.approx(0.7143, abs=0.001)

    def test_evidence_bonus_from_parent(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        parent = _make_hypothesis(
            statement="Parent",
            prior_confidence=0.7,
            certainty_of_evidence="high",
        )
        inv.add_hypothesis(parent)

        child = _make_hypothesis(
            statement="Child",
            prior_confidence=0.6,
            parent_id=parent.id,
            depth=1,
        )

        score = tm.compute_branch_score(child, inv)

        # 0.6 * (1/1.2) * 1.3 = 0.65
        expected = round(0.6 * (1.0 / 1.2) * 1.3, 4)
        assert score == expected

    def test_no_parent_no_bonus(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(prior_confidence=0.5, depth=1)

        score = tm.compute_branch_score(h, inv)

        # 0.5 * (1/1.2) * 1.0 = 0.4167
        expected = round(0.5 * (1.0 / 1.2), 4)
        assert score == expected

    def test_very_low_evidence_penalizes(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        parent = _make_hypothesis(
            statement="Weak parent",
            certainty_of_evidence="very_low",
        )
        inv.add_hypothesis(parent)

        child = _make_hypothesis(
            statement="Child",
            prior_confidence=0.5,
            parent_id=parent.id,
        )

        score = tm.compute_branch_score(child, inv)

        # 0.5 * 1.0 * 0.7 = 0.35
        assert score == 0.35


class TestApplyEvaluation:
    def test_deepen_creates_child_at_depth_plus_one(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(statement="Original", depth=1)
        inv.add_hypothesis(h)

        evaluation = {
            "action": "deepen",
            "revision": "Narrower sub-hypothesis",
            "confidence": 0.7,
        }

        new = tm.apply_evaluation(h, evaluation, inv)

        assert len(new) == 1
        assert new[0].statement == "Narrower sub-hypothesis"
        assert new[0].depth == 2
        assert new[0].parent_id == h.id
        assert h.id in new[0].parent_id
        assert new[0].id in h.children

    def test_branch_creates_sibling_at_same_depth(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(statement="Original", depth=1)
        inv.add_hypothesis(h)

        evaluation = {
            "action": "branch",
            "revision": "Alternative approach",
            "confidence": 0.5,
        }

        new = tm.apply_evaluation(h, evaluation, inv)

        assert len(new) == 1
        assert new[0].statement == "Alternative approach"
        assert new[0].depth == 1  # same depth
        assert new[0].parent_id == h.id
        assert new[0].id in h.children

    def test_prune_marks_rejected(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(statement="Bad hypothesis", status=HypothesisStatus.REVISED)

        evaluation = {"action": "prune"}

        new = tm.apply_evaluation(h, evaluation, inv)

        assert new == []
        assert h.status == HypothesisStatus.REJECTED

    def test_prune_does_not_override_supported(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(status=HypothesisStatus.SUPPORTED)

        evaluation = {"action": "prune"}

        tm.apply_evaluation(h, evaluation, inv)

        assert h.status == HypothesisStatus.SUPPORTED

    def test_prune_does_not_override_refuted(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(status=HypothesisStatus.REFUTED)

        evaluation = {"action": "prune"}

        tm.apply_evaluation(h, evaluation, inv)

        assert h.status == HypothesisStatus.REFUTED

    def test_deepen_without_revision_returns_empty(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis()

        evaluation = {"action": "deepen"}

        new = tm.apply_evaluation(h, evaluation, inv)

        assert new == []
        assert len(h.children) == 0

    def test_branch_without_revision_returns_empty(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis()

        evaluation = {"action": "branch"}

        new = tm.apply_evaluation(h, evaluation, inv)

        assert new == []

    def test_backward_compat_no_action_defaults_to_prune(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(status=HypothesisStatus.TESTING)

        evaluation = {"status": "refuted", "confidence": 0.1}

        new = tm.apply_evaluation(h, evaluation, inv)

        assert new == []
        assert h.status == HypothesisStatus.REJECTED

    def test_new_hypothesis_gets_branch_score(self) -> None:
        tm = TreeManager()
        inv = Investigation(prompt="test")
        h = _make_hypothesis(prior_confidence=0.7, depth=0)
        inv.add_hypothesis(h)

        evaluation = {
            "action": "deepen",
            "revision": "Deeper hypothesis",
            "confidence": 0.6,
        }

        new = tm.apply_evaluation(h, evaluation, inv)

        assert len(new) == 1
        assert new[0].branch_score > 0.0


class TestShouldContinue:
    def test_true_with_proposed_below_max_depth(self) -> None:
        tm = TreeManager(max_depth=3)
        hypotheses = [
            _make_hypothesis(status=HypothesisStatus.SUPPORTED),
            _make_hypothesis(status=HypothesisStatus.PROPOSED, depth=1),
        ]

        assert tm.should_continue(hypotheses) is True

    def test_false_with_no_proposed(self) -> None:
        tm = TreeManager()
        hypotheses = [
            _make_hypothesis(status=HypothesisStatus.SUPPORTED),
            _make_hypothesis(status=HypothesisStatus.REFUTED),
        ]

        assert tm.should_continue(hypotheses) is False

    def test_false_when_all_proposed_at_max_depth(self) -> None:
        tm = TreeManager(max_depth=2)
        hypotheses = [
            _make_hypothesis(status=HypothesisStatus.PROPOSED, depth=2),
            _make_hypothesis(status=HypothesisStatus.PROPOSED, depth=3),
        ]

        assert tm.should_continue(hypotheses) is False

    def test_true_with_empty_list(self) -> None:
        tm = TreeManager()

        assert tm.should_continue([]) is False
