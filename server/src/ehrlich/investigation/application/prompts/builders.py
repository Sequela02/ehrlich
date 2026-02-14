"""Non-director builder functions.

Haiku classification, literature survey, researcher prompt,
and uploaded-data context builders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.uploaded_file import UploadedFile


_DEFAULT_CATEGORIES = frozenset(
    {
        "antimicrobial",
        "neurodegenerative",
        "oncology",
        "environmental",
        "cardiovascular",
        "metabolic",
        "immunology",
        "other",
    }
)


def build_pico_and_classification_prompt(
    categories: frozenset[str] | None = None,
    uploaded_data_context: str = "",
) -> str:
    """Build a combined domain classification + PICO decomposition prompt.

    Single Haiku call replaces the old separate classification step.
    Produces domain category AND PICO framework for the literature survey.
    """
    cats = categories or _DEFAULT_CATEGORIES
    cats_with_other = cats | {"other"}
    cat_str = ", ".join(sorted(cats_with_other))
    return (
        "You are a scientific research analyst. Given a research prompt, "
        "perform TWO tasks:\n\n"
        "1. CLASSIFY the research domain into ALL relevant categories "
        "(at least 1, as many as apply).\n"
        "2. DECOMPOSE the research question using the PICO framework "
        "(Population, Intervention, Comparison, Outcome).\n\n"
        f"<categories>\n{cat_str}\n</categories>\n\n"
        "<instructions>\n"
        "- Domain: select every category that applies to the research question. "
        "Cross-domain questions (e.g. drug effects on athletic performance) "
        "should list all relevant categories.\n"
        "- Population: the subjects, organisms, or systems under study\n"
        "- Intervention: the treatment, compound, protocol, or variable being tested\n"
        "- Comparison: the control, baseline, or alternative being compared against\n"
        "- Outcome: the measurable result or endpoint of interest\n"
        "- Search terms: 3-5 broad search queries for literature discovery\n"
        "</instructions>\n\n"
        "<output_format>\n"
        "Respond with ONLY valid JSON (no markdown fences):\n"
        "{\n"
        '  "domain": ["category_1", "category_2"],\n'
        '  "population": "description of subjects/systems",\n'
        '  "intervention": "treatment/variable under study",\n'
        '  "comparison": "control/baseline",\n'
        '  "outcome": "measurable endpoint",\n'
        '  "search_terms": ["broad query 1", "broad query 2", "broad query 3"]\n'
        "}\n"
        "</output_format>" + (f"\n\n{uploaded_data_context}" if uploaded_data_context else "")
    )


def build_literature_survey_prompt(config: DomainConfig | None, pico: dict[str, Any]) -> str:
    """Build structured literature survey prompt with PICO context.

    Researcher gets domain-filtered tools and a structured protocol
    instead of the old throwaway 'search 3-6 times' instruction.
    """
    pop = pico.get("population", "")
    interv = pico.get("intervention", "")
    comp = pico.get("comparison", "")
    outcome = pico.get("outcome", "")
    terms = pico.get("search_terms", [])
    terms_str = ", ".join(f'"{t}"' for t in terms) if isinstance(terms, list) else str(terms)

    # Domain-specific search guidance
    domain_guidance = ""
    if config and config.tool_tags & {"training", "clinical"}:
        domain_guidance = (
            "\n<domain_sources>\n"
            "Training/clinical tools are available -- use multiple sources:\n"
            "- Use `search_pubmed_training` with MeSH terms for precise biomedical literature\n"
            "- Use `search_training_literature` for broader coverage via Semantic Scholar\n"
            "- Combine both sources for comprehensive evidence gathering\n"
            "</domain_sources>\n"
        )

    return (
        "You are a research scientist conducting a rapid scoping review "
        "(Arksey & O'Malley 2005) to map the evidence landscape.\n\n"
        "<pico_framework>\n"
        f"  Population: {pop}\n"
        f"  Intervention: {interv}\n"
        f"  Comparison: {comp}\n"
        f"  Outcome: {outcome}\n"
        f"  Initial search terms: {terms_str}\n"
        "</pico_framework>\n\n"
        "<search_protocol>\n"
        "Execute a multi-strategy search:\n\n"
        "1. DATABASE QUERIES: Use `search_literature` with broad terms first, "
        "then narrow based on results. Use `explore_dataset` or domain-specific "
        "search tools to find quantitative data.\n\n"
        "2. CITATION CHASING: For key papers found in step 1, use "
        "`search_citations` to find referenced and citing papers. "
        "Greenhalgh & Peacock (2005) found 51% of sources come from snowballing.\n\n"
        "3. SATURATION RULE: Stop when additional queries yield fewer than "
        "2 new unique results not already covered by previous searches.\n"
        "</search_protocol>\n\n" + domain_guidance + "<evidence_grading>\n"
        "When recording findings with `record_finding`, assign an evidence_level:\n"
        "  1 = Systematic review / meta-analysis\n"
        "  2 = Randomized controlled trial / large-scale validated study\n"
        "  3 = Cohort study / prospective observational\n"
        "  4 = Case-control study / retrospective analysis\n"
        "  5 = Case series / computational prediction / ML model\n"
        "  6 = Expert opinion / mechanistic reasoning\n"
        "  0 = Not applicable / unrated\n"
        "</evidence_grading>\n\n"
        "<rules>\n"
        "1. Record every significant finding with `record_finding` including "
        "evidence_level, source_type, and source_id.\n"
        "2. Use at least 2 different search strategies (database + citation chasing).\n"
        "3. Cite papers by DOI when referencing literature.\n"
        "4. Be quantitative: report exact numbers, effect sizes, sample sizes.\n"
        "5. Do NOT call `propose_hypothesis`, `design_experiment`, "
        "`evaluate_hypothesis`, or `conclude_investigation`.\n"
        "6. Stop after 6-10 tool calls or when search saturation is reached.\n"
        "</rules>"
    )


def build_literature_assessment_prompt() -> str:
    """Build Haiku prompt for body-of-evidence grading after literature survey.

    GRADE-adapted grading + AMSTAR-2-adapted self-assessment.
    """
    return (
        "You are a scientific evidence assessor. Given the findings from a "
        "literature survey, grade the overall body of evidence and assess "
        "the quality of the review process.\n\n"
        "<evidence_grading>\n"
        "Grade the body of evidence using GRADE-adapted criteria:\n"
        "- high: Consistent results from multiple high-quality studies (levels 1-2)\n"
        "- moderate: Results from well-designed studies with minor limitations\n"
        "- low: Results from observational studies or studies with significant limitations\n"
        "- very_low: Expert opinion only or severely limited evidence\n"
        "</evidence_grading>\n\n"
        "<self_assessment>\n"
        "Assess the review process against 4 rapid-review quality domains "
        "(adapted from AMSTAR 2):\n"
        "1. Protocol-guided search (PICO framework used)\n"
        "2. Multi-source search (more than 1 search strategy used)\n"
        "3. Evidence quality assessed (evidence levels assigned to findings)\n"
        "4. Transparent documentation (findings recorded with source provenance)\n"
        "Report which domains were satisfied and which were not.\n"
        "</self_assessment>\n\n"
        "<output_format>\n"
        "Respond with ONLY valid JSON (no markdown fences):\n"
        "{\n"
        '  "evidence_grade": "high|moderate|low|very_low",\n'
        '  "reasoning": "Brief justification for the grade",\n'
        '  "assessment": "Summary of which quality domains were met"\n'
        "}\n"
        "</output_format>"
    )


def build_researcher_prompt(
    config: DomainConfig,
    uploaded_data_context: str = "",
) -> str:
    """Build researcher experiment prompt adapted to the domain config."""
    examples = config.experiment_examples or ""
    return (
        "You are a research scientist executing a specific experiment "
        "to test a hypothesis in a scientific discovery investigation.\n\n"
        "<instructions>\n"
        "You have access to specialized tools for this domain. "
        "The user's research question defines the domain. "
        "Focus ONLY on the current experiment.\n\n"
        "Search strategy:\n"
        "- Start with short, broad queries to understand the landscape, "
        "then narrow focus based on results.\n\n"
        "Recording results:\n"
        "- Call `record_finding` after each significant discovery, "
        "always specifying hypothesis_id and evidence_type "
        "('supporting' or 'contradicting').\n"
        "- Include source_type and source_id for provenance tracing.\n"
        "- Be quantitative: report exact numbers, scores, and "
        "confidence intervals.\n\n"
        "Boundaries:\n"
        "- Do NOT call `conclude_investigation` -- the Director "
        "synthesizes results.\n"
        "- Do NOT call `propose_hypothesis`, `design_experiment`, or "
        "`evaluate_hypothesis` -- those are Director responsibilities.\n"
        "</instructions>\n\n"
        "<methodology>\n"
        "Apply these principles during experiment execution:\n\n"
        "1. SENSITIVITY: When training models or computing scores, test "
        "at least 2 parameter values. Flag results that change dramatically "
        "with small parameter changes as fragile.\n\n"
        "2. APPLICABILITY DOMAIN: For ML predictions, check if test "
        "compounds are similar to training data. Predictions far outside "
        "the training domain are unreliable -- note this when recording findings.\n\n"
        "3. UNCERTAINTY: Report ranges or mean +/- SD, not just point "
        "estimates. Note scoring function uncertainty where applicable.\n\n"
        "4. VERIFICATION: Before recording a finding, check if it makes "
        "physical sense. Verify inputs before passing to downstream tools.\n\n"
        "5. NEGATIVE RESULTS: Record failed approaches with a diagnosis "
        "of why they failed. A negative finding with evidence_type "
        "'contradicting' is scientifically valuable -- do not omit it.\n\n"
        "6. STATISTICAL TESTING: After gathering numeric comparison data, "
        "use `run_statistical_test` to formally compare two groups "
        "(auto-selects t-test/Welch/Mann-Whitney based on normality and "
        "variance). For count/categorical data, use `run_categorical_test` "
        "(auto-selects Fisher's exact or chi-squared). Record the result "
        "as a finding: evidence_type='supporting' if significant with "
        "meaningful effect size, 'contradicting' if non-significant or "
        "trivial effect.\n"
        "</methodology>\n\n"
        f"{examples}\n\n"
        "<rules>\n"
        "1. Explain your scientific reasoning before each tool call.\n"
        "2. Call `record_finding` after each significant discovery with "
        "hypothesis_id and evidence_type.\n"
        "3. Cite papers by DOI when referencing literature.\n"
        "4. If a tool returns an error, try an alternative approach.\n"
        "5. Be quantitative: report exact numbers and scores.\n"
        "6. Use at least 3 tool calls in this experiment.\n"
        "</rules>" + (f"\n\n{uploaded_data_context}" if uploaded_data_context else "")
    )


def build_uploaded_data_context(files: list[UploadedFile]) -> str:
    """Build XML context block describing user-uploaded files.

    Injected into Director and Researcher prompts so the model is aware
    of available datasets and can reference them via ``query_uploaded_data``.
    """
    if not files:
        return ""
    parts: list[str] = ["<uploaded_data>"]
    for f in files:
        if f.tabular:
            t = f.tabular
            cols = ", ".join(t.columns)
            dtypes = ", ".join(t.dtypes)
            parts.append(f'  <file id="{f.file_id}" name="{f.filename}" type="tabular">')
            parts.append(f"    Columns ({len(t.columns)}): {cols}")
            parts.append(f"    Dtypes: {dtypes}")
            parts.append(f"    Rows: {t.row_count}")
            if t.summary_stats:
                stats_lines = []
                for col_name, stats in list(t.summary_stats.items())[:6]:
                    mean = stats.get("mean", "?")
                    std = stats.get("std", "?")
                    stats_lines.append(f"{col_name}: mean={mean}, std={std}")
                parts.append(f"    Stats: {'; '.join(stats_lines)}")
            if t.sample_rows:
                header = " | ".join(t.columns)
                parts.append(f"    Sample: {header}")
                for row in t.sample_rows[:3]:
                    parts.append(f"            {' | '.join(row)}")
            parts.append("  </file>")
        elif f.document:
            d = f.document
            excerpt = d.text[:500] + "..." if len(d.text) > 500 else d.text
            parts.append(f'  <file id="{f.file_id}" name="{f.filename}" type="document">')
            parts.append(f"    Pages: {d.page_count}")
            parts.append(f"    Excerpt: {excerpt}")
            parts.append("  </file>")
    parts.append("</uploaded_data>")
    return "\n".join(parts)
