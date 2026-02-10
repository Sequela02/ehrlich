import json


async def record_finding(title: str, detail: str, evidence: str = "", phase: str = "") -> str:
    """Record a scientific finding during the investigation.

    Call this tool whenever you make a significant discovery or observation.
    Findings are accumulated throughout the investigation and included in the final report.
    """
    return json.dumps({"status": "recorded", "title": title, "phase": phase})


async def conclude_investigation(
    summary: str,
    candidates: list[dict[str, str]] | None = None,
    citations: list[str] | None = None,
) -> str:
    """Conclude the investigation with a summary, ranked candidates, and citations.

    Call this tool when all research phases are complete. Provide a comprehensive summary,
    a ranked list of candidate molecules, and full literature citations.
    """
    return json.dumps(
        {
            "status": "concluded",
            "summary": summary,
            "candidate_count": len(candidates) if candidates else 0,
            "citation_count": len(citations) if citations else 0,
        }
    )
