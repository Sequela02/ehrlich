import json
from pathlib import Path

from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.reference_set import CoreReferenceSet

_DEFAULT_PATH = Path(__file__).resolve().parents[5] / "data" / "references" / "core_references.json"


def load_core_references(path: Path | None = None) -> CoreReferenceSet:
    file_path = path or _DEFAULT_PATH
    if not file_path.exists():
        return CoreReferenceSet()
    with open(file_path) as f:
        data = json.load(f)

    papers_dict = data.get("papers", {})
    papers: list[Paper] = []
    key_index: dict[str, Paper] = {}

    for key, entry in papers_dict.items():
        paper = Paper(
            title=str(entry.get("title", "")),
            authors=list(entry.get("authors", [])),
            year=int(entry.get("year", 0)),
            abstract=str(entry.get("abstract", "")),
            doi=str(entry.get("doi", "")),
            source="core_reference",
        )
        papers.append(paper)
        key_index[key] = paper

    return CoreReferenceSet(papers=tuple(papers), _key_index=key_index)
