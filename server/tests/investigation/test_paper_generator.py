"""Tests for the scientific paper generator."""

from __future__ import annotations

import json

from ehrlich.investigation.application.paper_generator import extract_visualizations, generate_paper

# ── Fixtures ───────────────────────────────────────────────────────────

_PICO_EVENT = {
    "event_type": "literature_survey_completed",
    "event_data": json.dumps({
        "event": "literature_survey_completed",
        "data": {
            "pico": {
                "population": "MRSA clinical isolates",
                "intervention": "novel PBP2a inhibitors",
                "comparison": "vancomycin",
                "outcome": "minimum inhibitory concentration",
                "search_terms": ["MRSA", "PBP2a", "antimicrobial"],
            },
            "search_queries": 4,
            "total_results": 120,
            "included_results": 18,
            "evidence_grade": "moderate",
            "assessment": "Moderate evidence from 3 RCTs and 15 observational studies.",
            "investigation_id": "test-123",
        },
    }),
}

_EXPERIMENT_EVENT = {
    "event_type": "experiment_started",
    "event_data": json.dumps({
        "event": "experiment_started",
        "data": {
            "experiment_id": "exp-1",
            "hypothesis_id": "h1",
            "description": "Dock compounds against PBP2a",
            "independent_variable": "compound structure",
            "dependent_variable": "docking score",
            "controls": ["vancomycin"],
            "analysis_plan": "Compare docking scores",
            "investigation_id": "test-123",
        },
    }),
}

_EVAL_EVENT = {
    "event_type": "hypothesis_evaluated",
    "event_data": json.dumps({
        "event": "hypothesis_evaluated",
        "data": {
            "hypothesis_id": "h1",
            "status": "supported",
            "confidence": 0.85,
            "reasoning": "Docking scores below -7 kcal/mol for 3 candidates.",
            "certainty_of_evidence": "moderate",
            "investigation_id": "test-123",
        },
    }),
}

_TOOL_EVENTS = [
    {
        "event_type": "tool_called",
        "event_data": json.dumps({
            "event": "tool_called",
            "data": {"tool_name": "dock_compound", "investigation_id": "test-123"},
        }),
    },
    {
        "event_type": "tool_called",
        "event_data": json.dumps({
            "event": "tool_called",
            "data": {"tool_name": "dock_compound", "investigation_id": "test-123"},
        }),
    },
    {
        "event_type": "tool_called",
        "event_data": json.dumps({
            "event": "tool_called",
            "data": {"tool_name": "search_chembl", "investigation_id": "test-123"},
        }),
    },
]

_VALIDATION_EVENT = {
    "event_type": "validation_metrics",
    "event_data": json.dumps({
        "event": "validation_metrics",
        "data": {
            "z_prime": 0.72,
            "z_prime_quality": "excellent",
            "positive_control_count": 3,
            "negative_control_count": 5,
            "positive_mean": 0.88,
            "negative_mean": 0.12,
            "investigation_id": "test-123",
        },
    }),
}

_HYPOTHESES = [
    {
        "id": "h1",
        "statement": "Compound X inhibits PBP2a via active-site binding",
        "rationale": "Structural similarity to known inhibitors",
        "status": "supported",
        "confidence": 0.85,
        "certainty_of_evidence": "moderate",
        "supporting_evidence": ["Docking score -9.2 kcal/mol"],
        "contradicting_evidence": [],
    },
]

_EXPERIMENTS = [
    {
        "id": "exp-1",
        "hypothesis_id": "h1",
        "description": "Dock compounds against PBP2a",
        "tool_plan": ["dock_compound", "score_admet"],
        "status": "completed",
        "independent_variable": "compound structure",
        "dependent_variable": "docking score",
        "controls": ["vancomycin"],
        "confounders": ["solvent effects"],
        "analysis_plan": "Compare docking scores",
        "success_criteria": ">=3 compounds with docking < -7",
        "failure_criteria": "<2 compounds meet threshold",
    },
]

_FINDINGS = [
    {
        "title": "Strong binding affinity",
        "detail": "Docking score -9.2 kcal/mol against PBP2a",
        "hypothesis_id": "h1",
        "evidence_type": "supporting",
        "source_type": "pdb",
        "source_id": "2ABC",
    },
    {
        "title": "Poor ADMET profile",
        "detail": "LogP > 5 indicates poor oral bioavailability",
        "hypothesis_id": "h1",
        "evidence_type": "contradicting",
        "source_type": "chembl",
        "source_id": "CHEMBL25",
    },
]

_CANDIDATES = [
    {
        "identifier": "CC(=O)Oc1ccccc1C(=O)O",
        "identifier_type": "smiles",
        "name": "Aspirin",
        "rank": 1,
        "notes": "Top candidate",
        "scores": {"prediction_score": 0.92, "docking_score": -9.2},
        "attributes": {"resistance_risk": "low"},
    },
]

_NEGATIVE_CONTROLS = [
    {
        "identifier": "CCO",
        "name": "Ethanol",
        "score": 0.05,
        "threshold": 0.5,
        "correctly_classified": True,
        "source": "manual",
    },
]

_POSITIVE_CONTROLS = [
    {
        "identifier": "CC1=CC=CC=C1",
        "name": "Toluene",
        "known_activity": "Known PBP2a binder",
        "score": 0.9,
        "correctly_classified": True,
        "source": "literature",
    },
]

_CITATIONS = [
    "Smith et al. (2024) J Med Chem. doi:10.1021/jmc.2024.001",
    "Jones et al. (2023) Nature. doi:10.1038/s41586-023-002",
]

_COST_DATA = {
    "input_tokens": 50000,
    "output_tokens": 10000,
    "total_tokens": 60000,
    "total_cost_usd": 1.2345,
    "tool_calls": 15,
    "by_model": {
        "claude-opus-4-6": {
            "input_tokens": 30000,
            "output_tokens": 5000,
            "calls": 6,
            "cost_usd": 0.8,
        },
        "claude-sonnet-4-5-20250929": {
            "input_tokens": 15000,
            "output_tokens": 4000,
            "calls": 8,
            "cost_usd": 0.35,
        },
    },
}


def _all_events() -> list[dict[str, str]]:
    return [_PICO_EVENT, _EXPERIMENT_EVENT, _EVAL_EVENT, _VALIDATION_EVENT, *_TOOL_EVENTS]


def _full_paper() -> dict[str, str]:
    return generate_paper(
        investigation_id="test-123",
        prompt="Find novel antimicrobials against MRSA",
        summary="We identified 1 candidate compound with strong PBP2a binding.",
        domain="molecular_science",
        created_at="2026-02-14T12:00:00+00:00",
        hypotheses=_HYPOTHESES,
        experiments=_EXPERIMENTS,
        findings=_FINDINGS,
        candidates=_CANDIDATES,
        negative_controls=_NEGATIVE_CONTROLS,
        positive_controls=_POSITIVE_CONTROLS,
        citations=_CITATIONS,
        cost_data=_COST_DATA,
        events=_all_events(),
    )


# ── Tests ──────────────────────────────────────────────────────────────


class TestPaperStructure:
    """Paper contains all expected sections."""

    def test_has_all_section_keys(self) -> None:
        paper = _full_paper()
        expected = {
            "title", "abstract", "introduction", "methods",
            "results", "discussion", "references", "supplementary",
            "full_markdown",
        }
        assert expected == set(paper.keys())

    def test_full_markdown_contains_all_sections(self) -> None:
        paper = _full_paper()
        md = paper["full_markdown"]
        assert "# Find novel antimicrobials against MRSA" in md
        assert "## Abstract" in md
        assert "## 1. Introduction" in md
        assert "## 2. Methods" in md
        assert "## 3. Results" in md
        assert "## 4. Discussion" in md
        assert "## References" in md
        assert "## Supplementary Material" in md


class TestTitle:
    def test_contains_prompt(self) -> None:
        paper = _full_paper()
        assert "Find novel antimicrobials against MRSA" in paper["title"]

    def test_contains_domain(self) -> None:
        paper = _full_paper()
        assert "molecular_science" in paper["title"]

    def test_contains_date(self) -> None:
        paper = _full_paper()
        assert "2026-02-14" in paper["title"]

    def test_contains_id(self) -> None:
        paper = _full_paper()
        assert "test-123" in paper["title"]


class TestAbstract:
    def test_contains_summary(self) -> None:
        paper = _full_paper()
        assert "1 candidate compound" in paper["abstract"]

    def test_empty_summary(self) -> None:
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=[],
        )
        assert "No synthesis available" in paper["abstract"]


class TestIntroduction:
    def test_research_question(self) -> None:
        paper = _full_paper()
        assert "> Find novel antimicrobials against MRSA" in paper["introduction"]

    def test_pico_framework(self) -> None:
        paper = _full_paper()
        intro = paper["introduction"]
        assert "**Population:** MRSA clinical isolates" in intro
        assert "**Intervention:** novel PBP2a inhibitors" in intro
        assert "**Comparison:** vancomycin" in intro
        assert "**Outcome:** minimum inhibitory concentration" in intro

    def test_pico_search_terms(self) -> None:
        paper = _full_paper()
        assert "MRSA, PBP2a, antimicrobial" in paper["introduction"]

    def test_literature_survey(self) -> None:
        paper = _full_paper()
        intro = paper["introduction"]
        assert "120 found, 18 included" in intro
        assert "moderate" in intro

    def test_no_pico_when_no_events(self) -> None:
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="S",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=[],
        )
        assert "PICO" not in paper["introduction"]


class TestMethods:
    def test_experiment_description(self) -> None:
        paper = _full_paper()
        assert "Dock compounds against PBP2a" in paper["methods"]

    def test_variables(self) -> None:
        paper = _full_paper()
        methods = paper["methods"]
        assert "compound structure" in methods
        assert "docking score" in methods

    def test_controls(self) -> None:
        paper = _full_paper()
        assert "vancomycin" in paper["methods"]

    def test_tool_plan(self) -> None:
        paper = _full_paper()
        assert "dock_compound" in paper["methods"]

    def test_tool_usage_table(self) -> None:
        paper = _full_paper()
        methods = paper["methods"]
        assert "| dock_compound | 2 |" in methods
        assert "| search_chembl | 1 |" in methods

    def test_empty_experiments(self) -> None:
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="S",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=[],
        )
        assert "No experiments recorded" in paper["methods"]


class TestResults:
    def test_hypothesis_outcomes_table(self) -> None:
        paper = _full_paper()
        results = paper["results"]
        assert "supported" in results
        assert "85%" in results

    def test_findings_with_provenance(self) -> None:
        paper = _full_paper()
        results = paper["results"]
        assert "[pdb: 2ABC]" in results
        assert "[chembl: CHEMBL25]" in results

    def test_findings_grouped_by_type(self) -> None:
        paper = _full_paper()
        results = paper["results"]
        assert "Supporting Evidence (1)" in results
        assert "Contradicting Evidence (1)" in results

    def test_candidate_table(self) -> None:
        paper = _full_paper()
        results = paper["results"]
        assert "Aspirin" in results
        assert "0.92" in results


class TestDiscussion:
    def test_hypothesis_assessment(self) -> None:
        paper = _full_paper()
        disc = paper["discussion"]
        assert "Compound X inhibits PBP2a" in disc
        assert "**Status:** supported" in disc
        assert "85%" in disc

    def test_evaluation_reasoning_from_events(self) -> None:
        paper = _full_paper()
        disc = paper["discussion"]
        assert "Docking scores below -7 kcal/mol" in disc

    def test_supporting_evidence(self) -> None:
        paper = _full_paper()
        assert "Docking score -9.2 kcal/mol" in paper["discussion"]


class TestReferences:
    def test_citations(self) -> None:
        paper = _full_paper()
        refs = paper["references"]
        assert "Smith et al." in refs
        assert "Jones et al." in refs

    def test_data_sources(self) -> None:
        paper = _full_paper()
        refs = paper["references"]
        assert "pdb: 2ABC" in refs
        assert "chembl: CHEMBL25" in refs

    def test_empty_references(self) -> None:
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="S",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=[],
        )
        assert "No references collected" in paper["references"]


class TestSupplementary:
    def test_negative_controls(self) -> None:
        paper = _full_paper()
        supp = paper["supplementary"]
        assert "1/1 correctly classified" in supp
        assert "Ethanol" in supp

    def test_positive_controls(self) -> None:
        paper = _full_paper()
        supp = paper["supplementary"]
        assert "Known PBP2a binder" in supp
        assert "Toluene" in supp

    def test_validation_metrics(self) -> None:
        paper = _full_paper()
        supp = paper["supplementary"]
        assert "0.720" in supp
        assert "excellent" in supp

    def test_cost_breakdown(self) -> None:
        paper = _full_paper()
        supp = paper["supplementary"]
        assert "$1.2345" in supp
        assert "50,000" in supp

    def test_by_model_table(self) -> None:
        paper = _full_paper()
        supp = paper["supplementary"]
        assert "claude-opus-4-6" in supp
        assert "$0.8000" in supp


class TestEdgeCases:
    def test_empty_investigation(self) -> None:
        paper = generate_paper(
            investigation_id="empty", prompt="Empty test", summary="",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=[],
        )
        assert "# Empty test" in paper["title"]
        assert "No synthesis available" in paper["abstract"]
        assert "No experiments recorded" in paper["methods"]
        assert "No references collected" in paper["references"]
        assert paper["full_markdown"]

    def test_malformed_event_data_skipped(self) -> None:
        events = [{"event_type": "bad", "event_data": "not json{{{"}]
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="S",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=events,
        )
        assert paper["full_markdown"]

    def test_event_missing_data_key(self) -> None:
        events = [{"event_type": "tool_called", "event_data": json.dumps({"tool_name": "x"})}]
        paper = generate_paper(
            investigation_id="x", prompt="Q", summary="S",
            domain="", created_at="", hypotheses=[], experiments=[],
            findings=[], candidates=[], negative_controls=[],
            positive_controls=[], citations=[], cost_data={}, events=events,
        )
        assert paper["full_markdown"]


# ── Visualization Extraction Tests ────────────────────────────────────

_VIZ_EVENT_1 = {
    "event_type": "visualization",
    "event_data": json.dumps({
        "event": "visualization",
        "data": {
            "viz_type": "binding_scatter",
            "title": "Binding affinity vs LogP",
            "data": {"points": [{"x": 1, "y": 2}]},
            "config": {"xLabel": "LogP"},
        },
    }),
}

_VIZ_EVENT_2 = {
    "event_type": "visualization",
    "event_data": json.dumps({
        "event": "visualization",
        "data": {
            "viz_type": "forest_plot",
            "title": "Effect sizes",
            "data": {"studies": []},
            "config": {},
        },
    }),
}


class TestExtractVisualizations:
    def test_extracts_all_viz_events(self) -> None:
        events = [_PICO_EVENT, _VIZ_EVENT_1, *_TOOL_EVENTS, _VIZ_EVENT_2]
        vizs = extract_visualizations(events)
        assert len(vizs) == 2
        assert vizs[0]["viz_type"] == "binding_scatter"
        assert vizs[1]["viz_type"] == "forest_plot"

    def test_preserves_data_and_config(self) -> None:
        vizs = extract_visualizations([_VIZ_EVENT_1])
        assert vizs[0]["title"] == "Binding affinity vs LogP"
        assert vizs[0]["data"] == {"points": [{"x": 1, "y": 2}]}
        assert vizs[0]["config"] == {"xLabel": "LogP"}

    def test_empty_events_returns_empty(self) -> None:
        assert extract_visualizations([]) == []

    def test_no_viz_events_returns_empty(self) -> None:
        vizs = extract_visualizations(_all_events())
        assert vizs == []

    def test_malformed_viz_event_skipped(self) -> None:
        bad = {"event_type": "visualization", "event_data": "not json{"}
        vizs = extract_visualizations([bad, _VIZ_EVENT_1])
        assert len(vizs) == 1
