"""Tree manager for hypothesis exploration.

Decides which branches to explore, computes branch scores,
and processes Director evaluation actions (deepen/prune/branch).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from ehrlich.investigation.domain.hypothesis import Hypothesis, HypothesisStatus

if TYPE_CHECKING:
    from ehrlich.investigation.domain.investigation import Investigation


class TreeManager:
    """Manages tree-based hypothesis exploration strategy."""

    def __init__(self, max_depth: int = 3, prune_threshold: float = 0.3) -> None:
        self.max_depth = max_depth
        self.prune_threshold = prune_threshold

    def select_next(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        """Select up to 2 most promising PROPOSED hypotheses for testing.

        Priority: highest branch_score first, shallowest depth as tiebreak.
        Skips hypotheses at or beyond max_depth.
        """
        candidates = [
            h
            for h in hypotheses
            if h.status == HypothesisStatus.PROPOSED and h.depth < self.max_depth
        ]
        candidates.sort(key=lambda h: (-h.branch_score, h.depth))
        return candidates[:2]

    def compute_branch_score(self, hypothesis: Hypothesis, investigation: Investigation) -> float:
        """Compute exploration priority score for a hypothesis.

        score = prior_confidence * depth_discount * evidence_bonus

        depth_discount penalizes deep branches mildly.
        evidence_bonus rewards hypotheses whose parent had converging evidence.
        """
        base = hypothesis.prior_confidence if hypothesis.prior_confidence > 0 else 0.5
        depth_discount = 1.0 / (1 + hypothesis.depth * 0.2)

        evidence_bonus = 1.0
        if hypothesis.parent_id:
            parent = next(
                (h for h in investigation.hypotheses if h.id == hypothesis.parent_id),
                None,
            )
            if parent and parent.certainty_of_evidence:
                evidence_map = {"high": 1.3, "moderate": 1.1, "low": 0.9, "very_low": 0.7}
                evidence_bonus = evidence_map.get(parent.certainty_of_evidence, 1.0)

        return round(base * depth_discount * evidence_bonus, 4)

    def apply_evaluation(
        self,
        hypothesis: Hypothesis,
        evaluation: dict[str, Any],
        investigation: Investigation,
    ) -> list[Hypothesis]:
        """Process Director's evaluation and return new hypotheses to add.

        action="deepen": create sub-hypothesis from revision text at depth+1
        action="prune": mark hypothesis REJECTED, return empty
        action="branch": create revised hypothesis at same depth
        """
        action: str = evaluation.get("action", "prune")
        new_hypotheses: list[Hypothesis] = []

        if action == "deepen" and evaluation.get("revision"):
            child = Hypothesis(
                statement=evaluation["revision"],
                rationale=f"Deepened from: {hypothesis.statement[:80]}",
                id=str(uuid.uuid4())[:8],
                parent_id=hypothesis.id,
                depth=hypothesis.depth + 1,
                prior_confidence=evaluation.get("confidence", hypothesis.confidence),
            )
            child.branch_score = self.compute_branch_score(child, investigation)
            hypothesis.children.append(child.id)
            new_hypotheses.append(child)

        elif action == "branch" and evaluation.get("revision"):
            revised = Hypothesis(
                statement=evaluation["revision"],
                rationale=f"Branched from: {hypothesis.statement[:80]}",
                id=str(uuid.uuid4())[:8],
                parent_id=hypothesis.id,
                depth=hypothesis.depth,
                prior_confidence=evaluation.get("confidence", hypothesis.confidence),
            )
            revised.branch_score = self.compute_branch_score(revised, investigation)
            hypothesis.children.append(revised.id)
            new_hypotheses.append(revised)

        elif action == "prune":
            # Only mark REJECTED if not already terminally evaluated.
            # "prune" on a supported/refuted hypothesis just means
            # "stop exploring this branch" — no status change needed.
            if hypothesis.status not in (
                HypothesisStatus.SUPPORTED,
                HypothesisStatus.REFUTED,
            ):
                hypothesis.status = HypothesisStatus.REJECTED

        return new_hypotheses

    def should_continue(self, hypotheses: list[Hypothesis]) -> bool:
        """Return True if there are still explorable PROPOSED hypotheses."""
        return any(
            h.status == HypothesisStatus.PROPOSED and h.depth < self.max_depth for h in hypotheses
        )
