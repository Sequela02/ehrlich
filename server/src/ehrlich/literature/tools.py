import json


async def search_literature(query: str, limit: int = 10) -> str:
    """Search scientific literature for papers related to the query."""
    # TODO: Wire to LiteratureService
    return json.dumps({"status": "not_implemented", "query": query})


async def get_reference(doi: str) -> str:
    """Get a specific paper by DOI."""
    return json.dumps({"status": "not_implemented", "doi": doi})
