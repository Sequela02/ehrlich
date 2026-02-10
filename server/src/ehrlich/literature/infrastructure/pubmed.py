import contextlib
import logging
import xml.etree.ElementTree as ET

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.literature.domain.paper import Paper
from ehrlich.literature.domain.repository import PaperSearchRepository

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT = 15.0


class PubMedClient(PaperSearchRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(self, query: str, limit: int = 10) -> list[Paper]:
        try:
            pmids = await self._esearch(query, limit)
            if not pmids:
                return []
            return await self._efetch(pmids)
        except httpx.TimeoutException as e:
            raise ExternalServiceError("PubMed", f"Timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            raise ExternalServiceError("PubMed", f"HTTP {e.response.status_code}") from e

    async def get_by_doi(self, doi: str) -> Paper | None:
        results = await self.search(f"{doi}[DOI]", limit=1)
        return results[0] if results else None

    async def _esearch(self, query: str, limit: int) -> list[str]:
        resp = await self._client.get(
            _ESEARCH_URL,
            params={
                "db": "pubmed",
                "term": query,
                "retmax": min(limit, 100),
                "retmode": "json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("esearchresult", {})
        return list(result.get("idlist", []))

    async def _efetch(self, pmids: list[str]) -> list[Paper]:
        resp = await self._client.get(
            _EFETCH_URL,
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "rettype": "xml",
                "retmode": "xml",
            },
        )
        resp.raise_for_status()
        return self._parse_xml(resp.text)

    @staticmethod
    def _parse_xml(xml_text: str) -> list[Paper]:
        papers: list[Paper] = []
        root = ET.fromstring(xml_text)
        for article_el in root.findall(".//PubmedArticle"):
            medline = article_el.find("MedlineCitation")
            if medline is None:
                continue
            article = medline.find("Article")
            if article is None:
                continue

            title_el = article.find("ArticleTitle")
            title = title_el.text or "" if title_el is not None else ""

            authors: list[str] = []
            author_list = article.find("AuthorList")
            if author_list is not None:
                for author_el in author_list.findall("Author"):
                    last = author_el.findtext("LastName", "")
                    fore = author_el.findtext("ForeName", "")
                    if last:
                        name = f"{last}, {fore}" if fore else last
                        authors.append(name)

            abstract_el = article.find("Abstract/AbstractText")
            abstract = abstract_el.text or "" if abstract_el is not None else ""

            year = 0
            date_el = article.find("Journal/JournalIssue/PubDate/Year")
            if date_el is not None and date_el.text:
                with contextlib.suppress(ValueError):
                    year = int(date_el.text)

            doi = ""
            article_data = article_el.find("PubmedData")
            if article_data is not None:
                for id_el in article_data.findall(".//ArticleId"):
                    if id_el.get("IdType") == "doi" and id_el.text:
                        doi = id_el.text
                        break

            papers.append(
                Paper(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                    doi=doi,
                    source="pubmed",
                )
            )
        return papers
