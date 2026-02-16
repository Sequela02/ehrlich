"""Director-phase builder functions.

These generate domain-adaptive prompts for the Director model
using DomainConfig to customize hypothesis types, examples,
scoring instructions, and candidate labels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ehrlich.investigation.domain.domain_config import DomainConfig
    from ehrlich.investigation.domain.investigation import Investigation


def build_formulation_prompt(
    config: DomainConfig,
    uploaded_data_context: str = "",
) -> str:
    """Build Director formulation prompt adapted to the domain config."""
    hyp_types = "|".join(config.hypothesis_types) if config.hypothesis_types else "other"
    examples = config.director_examples or ""
    return (
        "You are the Director of a scientific discovery investigation. "
        "You formulate hypotheses and design the research strategy but "
        "do NOT execute tools yourself.\n\n"
        "<instructions>\n"
        "Given the user's research prompt and literature survey results, "
        "formulate 2-4 testable hypotheses. Each hypothesis must be:\n"
        "- Specific and falsifiable\n"
        "- Grounded in the literature findings provided\n"
        "- Testable with the available tools\n"
        "- Orthogonal to sibling hypotheses: each must attack a different "
        "mechanism, pathway, or data source\n\n"
        "Hypotheses tested in parallel must maximize scientific coverage:\n"
        "- Different causal mechanisms or molecular targets\n"
        "- Different primary data sources or tool chains\n"
        "- Different validation strategies (e.g., ML prediction vs "
        "structural docking vs substructure enrichment)\n"
        "Do NOT formulate hypotheses that would produce overlapping experiments.\n\n"
        "If prior investigation results are provided in "
        "<prior_investigations>, leverage their outcomes:\n"
        "- Build on supported hypotheses from related investigations\n"
        "- Avoid repeating refuted approaches\n"
        "- Consider candidates already identified as starting points\n\n"
        "Also identify 1-3 negative controls (subjects known to be "
        "inactive) AND 1-2 positive controls (subjects known to be "
        "active). Both are essential for validation: negative controls "
        "confirm specificity, positive controls confirm the pipeline "
        "can detect true actives. Without positive controls, pipeline "
        "failures are undetectable (Zhang et al., 1999).\n"
        "</instructions>\n\n"
        f"{examples}\n\n"
        "<output_format>\n"
        "Respond with ONLY valid JSON (no markdown fences):\n"
        "{\n"
        '  "hypotheses": [\n'
        "    {\n"
        '      "statement": "Specific testable hypothesis",\n'
        '      "rationale": "Causal mechanism explaining HOW and WHY",\n'
        '      "prediction": "If true, we expect to observe X",\n'
        '      "null_prediction": "If false, we would observe Y instead",\n'
        '      "success_criteria": "Quantitative threshold for support",\n'
        '      "failure_criteria": "Quantitative threshold for refutation",\n'
        '      "scope": "Boundary conditions",\n'
        f'      "hypothesis_type": "{hyp_types}",\n'
        '      "prior_confidence": 0.65\n'
        "    }\n"
        "  ],\n"
        '  "negative_controls": [\n'
        "    {\n"
        '      "identifier": "identifier of known inactive subject",\n'
        '      "name": "Name",\n'
        '      "source": "Why this is a good negative control"\n'
        "    }\n"
        "  ],\n"
        '  "positive_controls": [\n'
        "    {\n"
        '      "identifier": "identifier of known active subject",\n'
        '      "name": "Name",\n'
        '      "known_activity": "IC50 = X nM against target Y",\n'
        '      "source": "Why this is a good positive control"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "</output_format>" + (f"\n\n{uploaded_data_context}" if uploaded_data_context else "")
    )


def build_experiment_prompt(
    config: DomainConfig,
    uploaded_data_context: str = "",
) -> str:
    """Build Director experiment design prompt adapted to the domain config."""
    examples = config.experiment_examples or ""
    return (
        "You are the Director designing an experiment to test a "
        "hypothesis in a scientific discovery investigation.\n\n"
        "<instructions>\n"
        "Given the hypothesis and available tools, design a structured "
        "experiment protocol with:\n"
        "- A clear description of what the experiment will test\n"
        "- An ordered tool_plan listing the tools to execute\n"
        "- Defined variables, controls, and analysis plan\n"
        "</instructions>\n\n"
        "<methodology>\n"
        "Follow these 5 principles when designing experiments:\n\n"
        "1. VARIABLES: Define the independent variable (factor being "
        "manipulated) and dependent variable (outcome being measured). "
        "Be specific about units and measurement method.\n\n"
        "2. CONTROLS: Include at least one positive or negative baseline. "
        "Positive controls confirm the assay works (known active). "
        "Negative controls confirm specificity (known inactive).\n\n"
        "3. CONFOUNDERS: Identify threats to validity. Common confounders: "
        "dataset bias, assay type mismatch, species differences, "
        "structural similarity to training data.\n\n"
        "4. ANALYSIS PLAN: Pre-specify metrics and thresholds BEFORE "
        "seeing results. This prevents post-hoc rationalization. "
        "Include: primary metric, threshold, and sample size expectation. "
        "When comparing two groups of numeric data, plan a statistical "
        "test: specify `run_statistical_test` (continuous) or "
        "`run_categorical_test` (categorical) in the tool_plan, with "
        "alpha level and minimum effect size threshold as part of "
        "success_criteria.\n\n"
        "5. SENSITIVITY: Consider robustness. Will the conclusion change "
        "if you vary a key parameter by +/- 20%? Note fragile assumptions.\n"
        "</methodology>\n\n"
        f"{examples}\n\n"
        "<output_format>\n"
        "Respond with ONLY valid JSON (no markdown fences):\n"
        "{\n"
        '  "description": "What this experiment will do",\n'
        '  "tool_plan": ["tool_name_1", "tool_name_2"],\n'
        '  "independent_variable": "Factor being manipulated",\n'
        '  "dependent_variable": "Outcome being measured",\n'
        '  "controls": ["positive: known active", "negative: known inactive"],\n'
        '  "confounders": ["identified threats to validity"],\n'
        '  "analysis_plan": "Pre-specified metrics and thresholds",\n'
        '  "success_criteria": "What result would support the hypothesis",\n'
        '  "failure_criteria": "What result would refute the hypothesis"\n'
        "}\n"
        "</output_format>" + (f"\n\n{uploaded_data_context}" if uploaded_data_context else "")
    )


def build_synthesis_prompt(config: DomainConfig) -> str:
    """Build Director synthesis prompt adapted to the domain config.

    Includes GRADE-adapted certainty grading, recommendation strength (priority
    tiers 1-4), structured limitations taxonomy, knowledge gap analysis, and
    follow-up experiment recommendations.
    """
    scoring = config.synthesis_scoring_instructions or ""
    label = config.candidate_label or "Candidates"
    return (
        "You are the Director synthesizing the full investigation "
        "results into a final report.\n\n"
        "<instructions>\n"
        "Review all hypothesis outcomes, findings, and negative controls "
        "to produce a comprehensive synthesis. Your report must:\n"
        "- Summarize hypothesis outcomes with confidence levels\n"
        f"- Rank {label.lower()} by multi-criteria evidence strength\n"
        "- Assess model reliability using negative AND positive control results\n"
        "- Identify limitations and suggest follow-up experiments\n"
        "- Include all relevant citations\n\n"
        "<validation_quality>\n"
        "Assess model/prediction validation quality:\n\n"
        "1. CONTROL SEPARATION: Are positive control scores clearly separated "
        "from negative control scores? If positive controls scored below the "
        "active threshold, the model is unreliable -- flag this prominently.\n\n"
        "2. CLASSIFICATION QUALITY: With the available controls, assess whether "
        "the model can discriminate actives from inactives. Consider:\n"
        "- Do all positive controls score above threshold? (sensitivity check)\n"
        "- Do all negative controls score below threshold? (specificity check)\n"
        "- Is there clear separation between control groups?\n\n"
        "3. OVERALL VALIDATION: Rate as:\n"
        '- "sufficient": positive controls pass, negatives pass, clear separation\n'
        '- "marginal": most controls pass but separation is narrow\n'
        '- "insufficient": any positive control fails, or no positive controls tested\n\n'
        "4. Z'-FACTOR: Z' >= 0.5 = excellent assay separation, "
        "0 < Z' < 0.5 = marginal (scores overlap), "
        "Z' <= 0 = unusable (no separation between controls). "
        "If Z'-factor is provided, cite it explicitly in your validation assessment.\n\n"
        "5. PERMUTATION SIGNIFICANCE: If permutation_p_value < 0.05, the model is "
        "significantly better than random. If p >= 0.05, predictions may be noise -- "
        "flag this prominently.\n\n"
        "6. SCAFFOLD-SPLIT GAP: If the gap between random_auroc and scaffold AUROC is "
        "> 0.15, the model may be memorizing scaffolds rather than learning activity. "
        "Report this as a methodology limitation.\n\n"
        "If validation is insufficient, downgrade certainty of ALL hypothesis "
        "assessments by one level and note this in limitations.\n"
        "</validation_quality>\n\n"
        "<certainty_grading>\n"
        "For each hypothesis assessment, assign a GRADE-adapted certainty level:\n"
        "- high: Multiple concordant methods, strong controls, large effect sizes, "
        "evidence from tiers 1-3\n"
        "- moderate: Some concordance, adequate controls, moderate effect sizes\n"
        "- low: Few methods, weak controls, small or inconsistent effects\n"
        "- very_low: Single method, no controls, conflicting evidence\n\n"
        "Five domains that DOWNGRADE certainty:\n"
        "1. Risk of bias: poor model validation, outside applicability domain\n"
        "2. Inconsistency: methods disagree (docking vs ML vs literature)\n"
        "3. Indirectness: evidence from different target/species/assay than asked\n"
        "4. Imprecision: wide confidence intervals, small sample sizes\n"
        "5. Publication bias: database coverage gaps, missing negative results\n\n"
        "Three domains that can UPGRADE (for computational evidence):\n"
        "1. Large effect: very strong activity (>10-fold over baseline)\n"
        "2. Dose-response: clear SAR gradient across compound series\n"
        "3. Conservative prediction: result holds despite known biases\n\n"
        "Name which domains caused downgrading or upgrading in certainty_reasoning.\n"
        "</certainty_grading>\n\n"
        "<recommendation_strength>\n"
        "Assign each candidate a priority tier based on certainty, evidence, and risk:\n\n"
        "Priority 1 (Strong Advance): High or moderate certainty. Multiple supported "
        "hypotheses. Concordant methods. Controls pass. Large effects. "
        "Action: queue for experimental testing.\n\n"
        "Priority 2 (Conditional Advance): Moderate or low certainty. 1-2 supported "
        "hypotheses. Some method concordance. Adequate controls. "
        "Action: additional computational validation.\n\n"
        "Priority 3 (Watchlist): Low certainty. Partial support, limited methods, "
        "or borderline activity. "
        "Action: investigate further computationally; low resource priority.\n\n"
        "Priority 4 (Do Not Advance): Very low certainty. Refuted hypotheses, "
        "control failures, contradictory evidence, or safety flags. "
        "Action: archive; redirect effort.\n"
        "</recommendation_strength>\n\n"
        "<limitations_taxonomy>\n"
        "Report limitations using these four categories:\n"
        "- methodology: model limitations, scoring function inaccuracy, "
        "conformational sampling, feature representation\n"
        "- data: database coverage gaps, assay heterogeneity, activity cliffs, "
        "publication bias, missing data types\n"
        "- scope: in silico only, limited chemical space, time-bound investigation, "
        "single-target focus\n"
        "- interpretation: scores are rank-ordering not absolute, "
        "ML probabilities need calibration, predictions based on known data only\n"
        "</limitations_taxonomy>\n\n"
        "<knowledge_gaps>\n"
        "Identify what evidence was NOT collected during this investigation. "
        "Construct a conceptual evidence map: for each hypothesis, which evidence "
        "types are present and which are missing?\n\n"
        "Classify each gap:\n"
        "- evidence: no data available\n"
        "- quality: data exists but low quality\n"
        "- consistency: conflicting results across methods\n"
        "- scope: evidence exists but for different context\n"
        "- temporal: evidence outdated\n"
        "</knowledge_gaps>\n\n"
        "<follow_up>\n"
        "Recommend specific next experiments prioritized by impact on confidence. "
        "For each recommendation, specify:\n"
        "- What to do and why it matters\n"
        "- Whether it is computational or experimental\n"
        "- Impact level: critical, high, medium, or low\n"
        "</follow_up>\n\n"
        f"{scoring}\n"
        "</instructions>\n\n"
        "<output_format>\n"
        "Respond with ONLY valid JSON (no markdown fences):\n"
        "{\n"
        '  "summary": "Comprehensive 2-3 paragraph summary",\n'
        '  "candidates": [\n'
        "    {\n"
        '      "identifier": "identifier string",\n'
        '      "identifier_type": "' + config.identifier_type + '",\n'
        '      "name": "name",\n'
        '      "rationale": "why this candidate is promising",\n'
        '      "rank": 1,\n'
        '      "priority": 1,\n'
        '      "scores": [{"name": "score_name", "value": 0.85}],\n'
        '      "attributes": [{"name": "attr_name", "value": "attr_value"}]\n'
        "    }\n"
        "  ],\n"
        '  "citations": ["DOI or reference strings"],\n'
        '  "hypothesis_assessments": [\n'
        "    {\n"
        '      "hypothesis_id": "h1",\n'
        '      "statement": "the hypothesis",\n'
        '      "status": "supported|refuted|revised",\n'
        '      "confidence": 0.85,\n'
        '      "certainty": "high|moderate|low|very_low",\n'
        '      "certainty_reasoning": "downgraded by X, upgraded by Y",\n'
        '      "key_evidence": "summary of evidence"\n'
        "    }\n"
        "  ],\n"
        '  "negative_control_summary": "Summary of negative control results",\n'
        '  "model_validation_quality": "sufficient|marginal|insufficient",\n'
        '  "confidence": "high/medium/low",\n'
        '  "limitations": [\n'
        "    {\n"
        '      "category": "methodology|data|scope|interpretation",\n'
        '      "description": "specific limitation"\n'
        "    }\n"
        "  ],\n"
        '  "knowledge_gaps": [\n'
        "    {\n"
        '      "gap_type": "evidence|quality|consistency|scope|temporal",\n'
        '      "description": "what is missing and why it matters"\n'
        "    }\n"
        "  ],\n"
        '  "follow_up_experiments": [\n'
        "    {\n"
        '      "description": "what to do next",\n'
        '      "impact": "critical|high|medium|low",\n'
        '      "type": "computational|experimental"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "</output_format>"
    )


def build_multi_investigation_context(
    investigations: list[Investigation],
) -> str:
    """Compress past completed investigations into XML context for the Director."""
    if not investigations:
        return ""
    parts: list[str] = ["<prior_investigations>"]
    for inv in investigations[:3]:
        parts.append(f'  <investigation domain="{inv.domain}" prompt="{inv.prompt[:100]}">')
        for h in inv.hypotheses[:4]:
            if h.status.value in ("supported", "refuted", "revised"):
                parts.append(
                    f"    <hypothesis status='{h.status.value}' "
                    f"confidence='{h.confidence:.0%}'>"
                    f"{h.statement}</hypothesis>"
                )
        for c in inv.candidates[:2]:
            top_score = max(c.scores.values()) if c.scores else 0
            parts.append(
                f"    <candidate rank='{c.rank}' "
                f"identifier='{c.identifier}' score='{top_score:.2f}'>"
                f"{c.name or 'unnamed'}</candidate>"
            )
        if inv.summary:
            parts.append(f"    <summary>{inv.summary[:300]}</summary>")
        parts.append("  </investigation>")
    parts.append("</prior_investigations>")
    return "\n".join(parts)
