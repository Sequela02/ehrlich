from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient


class TestSemanticScholarParsing:
    def test_to_paper_full(self) -> None:
        data = {
            "title": "Test Paper",
            "authors": [{"name": "Smith, J."}, {"name": "Doe, A."}],
            "year": 2024,
            "abstract": "Test abstract.",
            "externalIds": {"DOI": "10.1234/test"},
            "citationCount": 42,
        }
        paper = SemanticScholarClient._to_paper(data)
        assert paper.title == "Test Paper"
        assert paper.authors == ["Smith, J.", "Doe, A."]
        assert paper.year == 2024
        assert paper.abstract == "Test abstract."
        assert paper.doi == "10.1234/test"
        assert paper.citations == 42
        assert paper.source == "semantic_scholar"

    def test_to_paper_missing_fields(self) -> None:
        data = {"title": "Minimal"}
        paper = SemanticScholarClient._to_paper(data)
        assert paper.title == "Minimal"
        assert paper.authors == []
        assert paper.year == 0
        assert paper.doi == ""

    def test_to_paper_null_abstract(self) -> None:
        data = {"title": "Test", "abstract": None, "year": None}
        paper = SemanticScholarClient._to_paper(data)
        assert paper.abstract == ""
        assert paper.year == 0
