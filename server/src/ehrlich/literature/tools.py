import json

from ehrlich.literature.application.literature_service import LiteratureService
from ehrlich.literature.infrastructure.reference_loader import load_core_references
from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient

_references = load_core_references()
_service = LiteratureService(
    primary=SemanticScholarClient(),
    references=_references,
)


async def search_literature(query: str, limit: int = 10) -> str:
    """Search scientific literature for papers related to the query."""
    papers = await _service.search_papers(query, limit)
    results = []
    for p in papers:
        results.append(
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "abstract": p.abstract[:500] if p.abstract else "",
                "citations": p.citations,
                "citation": _service.format_citation(p),
            }
        )
    return json.dumps({"query": query, "count": len(results), "papers": results})


async def search_citations(
    paper_id: str, direction: str = "both", limit: int = 10
) -> str:
    """Search for papers that cite or are referenced by a given paper.

    Use this for citation chasing (snowballing) to discover related work.
    Greenhalgh & Peacock (2005) found 51% of sources come from snowballing.

    Args:
        paper_id: Semantic Scholar paper ID or DOI (e.g. "10.1038/s41586-024-07613-w")
        direction: 'references' (cited by this paper), 'citing' (cite this paper), or 'both'
        limit: Maximum papers to return per direction (default 10)
    """
    papers = await _service.search_citations(paper_id, direction, limit)
    results = []
    for p in papers:
        results.append(
            {
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "doi": p.doi,
                "abstract": p.abstract[:500] if p.abstract else "",
                "citations": p.citations,
                "citation": _service.format_citation(p),
            }
        )
    return json.dumps(
        {"paper_id": paper_id, "direction": direction, "count": len(results), "papers": results}
    )


async def get_reference(key: str) -> str:
    """Get a reference by key (halicin, abaucin, chemprop, pkcsm, who_bppl_2024) or DOI."""
    paper = await _service.get_reference(key)
    if paper is None:
        available = _service.list_reference_keys()
        return json.dumps({"error": f"Reference not found: {key}", "available_keys": available})
    return json.dumps(
        {
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "doi": paper.doi,
            "abstract": paper.abstract,
            "citation": _service.format_citation(paper),
        }
    )
