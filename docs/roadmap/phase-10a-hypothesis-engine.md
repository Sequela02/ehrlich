Back to [Roadmap Index](README.md)

# Phase 10A: Hypothesis-Driven Investigation Engine (Feb 10) -- DONE

Replaced the linear 7-phase pipeline with a hypothesis-driven scientific method loop.

## Architecture Change
- **Old:** Literature -> Data -> Model -> Screen -> Structure -> Resistance -> Conclude (linear recipe)
- **New:** Literature Survey -> Formulate Hypotheses -> For each: Design Experiment -> Execute -> Evaluate -> Negative Controls -> Synthesize

## Domain Layer
- [x] `Hypothesis` entity: statement, rationale, status (proposed/testing/supported/refuted/revised), confidence, evidence lists
- [x] `Experiment` entity: hypothesis_id, description, tool_plan, status, result_summary
- [x] `NegativeControl` frozen dataclass: identifier, identifier_type, score, threshold, correctly_classified property (generalized in Domain-Agnostic phase)
- [x] `Finding` modified: `hypothesis_id` + `evidence_type` replace `phase`
- [x] `Investigation` modified: hypotheses, experiments, negative_controls replace phases

## Events (12 total, was 11)
- [x] Removed: `PhaseStarted`, `PhaseCompleted`, `DirectorPlanning`, `DirectorDecision`
- [x] Added: `HypothesisFormulated`, `ExperimentStarted`, `ExperimentCompleted`, `HypothesisEvaluated`, `NegativeControlRecorded`
- [x] Modified: `FindingRecorded` (hypothesis_id + evidence_type), `InvestigationCompleted` (hypotheses + negative_controls)

## Tools (23 total, was 19)
- [x] 4 new control tools: `propose_hypothesis`, `design_experiment`, `evaluate_hypothesis`, `record_negative_control`
- [x] Modified: `record_finding` (hypothesis_id + evidence_type), `conclude_investigation` (hypothesis assessments)

## Orchestrators
- [x] Single-model `Orchestrator`: hypothesis control tool dispatch with entity creation
- [x] `MultiModelOrchestrator`: hypothesis-driven loop (formulate -> design -> execute -> evaluate per hypothesis)
- [x] 7 hypothesis-driven prompts replacing 6 phase-based prompts

## Console
- [x] `HypothesisBoard` + `HypothesisCard`: kanban-style status grid with confidence bars
- [x] `ActiveExperimentCard`: replaces `ActivePhaseCard` with experiment context
- [x] `NegativeControlPanel`: validation table with pass/fail indicators
- [x] `FindingsPanel`: evidence type badges + hypothesis grouping
- [x] `Timeline`: hypothesis/experiment/evaluation event rendering
- [x] Deleted: `PhaseProgress.tsx`, `ActivePhaseCard.tsx`

## Persistence
- [x] SQLite schema: hypotheses, experiments, negative_controls columns (JSON serialized)
- [x] Removed: phases, current_phase columns

**Verification:** 212 tests passed, mypy 0 errors, ruff 0 violations, tsc 0 errors, bun build success.

---

## Scientific Methodology Upgrade (Cross-Cutting)

Grounding every phase of the investigation workflow in established scientific methodology. Each phase gets the treatment that Phase 1 (Hypothesis) received: deep research, universal components, entity upgrades, prompt updates. See [`docs/scientific-methodology.md`](../scientific-methodology.md) for full details.

| # | Phase | Status |
|---|-------|--------|
| 1 | Hypothesis Formulation (Popper, Platt, Feynman, Bayesian) | DONE |
| 2 | Literature Survey (PICO, citation chasing, GRADE, AMSTAR-2) | DONE |
| 3 | Experiment Design (Fisher, controls, sensitivity, AD) | DONE |
| 4 | Evidence Evaluation (evidence hierarchy, GRADE, effect sizes) | DONE |
| 5 | Negative Controls (Z'-factor, permutation significance, scaffold-split) | DONE |
| 6 | Synthesis (GRADE certainty, priority tiers, knowledge gaps) | DONE |
