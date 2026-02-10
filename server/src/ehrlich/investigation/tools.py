import json


async def record_finding(title: str, detail: str, evidence: str = "", phase: str = "") -> str:
    """Record a scientific finding during the investigation."""
    return json.dumps({"status": "recorded", "title": title})


async def conclude_investigation(summary: str, candidate_count: int = 0) -> str:
    """Conclude the investigation with a summary."""
    return json.dumps({"status": "concluded", "summary": summary})
