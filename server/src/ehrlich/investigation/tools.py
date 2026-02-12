import json


async def record_finding(
    title: str,
    detail: str,
    hypothesis_id: str = "",
    evidence_type: str = "neutral",
    evidence: str = "",
    source_type: str = "",
    source_id: str = "",
    evidence_level: int = 0,
) -> str:
    """Record a scientific finding linked to a hypothesis.

    Call this tool whenever you make a significant discovery or observation.
    Findings are accumulated throughout the investigation and included in the final report.

    Args:
        title: Short title of the finding
        detail: Detailed description of the finding
        hypothesis_id: ID of the hypothesis this finding relates to
        evidence_type: One of 'supporting', 'contradicting', or 'neutral'
        evidence: Raw evidence data or citation
        source_type: Data source type (chembl, pdb, doi, pubchem, uniprot, opentargets, gtopdb)
        source_id: Specific identifier from the source (e.g. CHEMBL25, 2ABC, 10.1038/...)
        evidence_level: Evidence hierarchy 0-6 (0=unrated, 1-6 per evidence pyramid)
    """
    return json.dumps({"status": "recorded", "title": title, "hypothesis_id": hypothesis_id})


async def conclude_investigation(
    summary: str,
    candidates: list[dict[str, str]] | None = None,
    citations: list[str] | None = None,
    hypothesis_assessments: list[dict[str, str]] | None = None,
    negative_control_summary: str = "",
) -> str:
    """Conclude the investigation with a summary, ranked candidates, and hypothesis assessments.

    Call this tool when all hypotheses have been tested and evaluated.

    Args:
        summary: Comprehensive summary of the investigation
        candidates: Ranked list of candidates with identifiers and scores
        citations: Full literature citations with DOIs
        hypothesis_assessments: Summary of each hypothesis outcome
        negative_control_summary: Summary of negative control validation results
    """
    return json.dumps(
        {
            "status": "concluded",
            "summary": summary,
            "candidate_count": len(candidates) if candidates else 0,
            "citation_count": len(citations) if citations else 0,
        }
    )


async def propose_hypothesis(
    statement: str,
    rationale: str,
    parent_id: str = "",
) -> str:
    """Propose a testable scientific hypothesis.

    Call this to register a hypothesis that will be tested through experiments.
    Each hypothesis should be specific, testable, and falsifiable.

    Args:
        statement: The testable hypothesis statement
        rationale: Scientific reasoning supporting this hypothesis
        parent_id: ID of parent hypothesis if this is a revision
    """
    return json.dumps({"status": "proposed", "statement": statement})


async def design_experiment(
    hypothesis_id: str,
    description: str,
    tool_plan: list[str] | None = None,
) -> str:
    """Design an experiment to test a specific hypothesis.

    Call this to plan what tools and analyses will be used to test the hypothesis.

    Args:
        hypothesis_id: ID of the hypothesis to test
        description: What the experiment will do and what success/failure looks like
        tool_plan: List of tool names to be used in order
    """
    return json.dumps(
        {
            "status": "designed",
            "hypothesis_id": hypothesis_id,
            "tool_count": len(tool_plan) if tool_plan else 0,
        }
    )


async def evaluate_hypothesis(
    hypothesis_id: str,
    status: str,
    confidence: float,
    reasoning: str,
) -> str:
    """Evaluate a hypothesis based on experimental evidence.

    Call this after experiments are complete to assess whether the hypothesis is
    supported, refuted, or needs revision.

    Args:
        hypothesis_id: ID of the hypothesis to evaluate
        status: One of 'supported', 'refuted', or 'revised'
        confidence: Confidence level 0.0-1.0
        reasoning: Scientific reasoning for the assessment
    """
    return json.dumps(
        {
            "status": "evaluated",
            "hypothesis_id": hypothesis_id,
            "outcome": status,
            "confidence": confidence,
        }
    )


async def record_negative_control(
    identifier: str,
    name: str,
    score: float,
    threshold: float = 0.5,
    identifier_type: str = "",
    source: str = "",
) -> str:
    """Record a negative control prediction for model validation.

    Call this to validate model reliability by testing known inactive subjects.
    A good model should predict low scores for negative controls.

    Args:
        identifier: Identifier of the control subject (SMILES, protocol name, etc.)
        name: Name of the control subject
        score: Model's predicted activity score (0-1)
        threshold: Score threshold for classification (default 0.5)
        identifier_type: Type of identifier (smiles, protocol, compound_name)
        source: Where this negative control was sourced from
    """
    correctly_classified = score < threshold
    return json.dumps(
        {
            "status": "recorded",
            "name": name,
            "score": score,
            "correctly_classified": correctly_classified,
        }
    )
