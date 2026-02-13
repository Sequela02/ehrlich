from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.training.domain.entities import PubMedArticle
from ehrlich.training.domain.repository import PubMedRepository

logger = logging.getLogger(__name__)

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class PubMedClient(PubMedRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, query: str, mesh_terms: list[str] | None = None, max_results: int = 10
    ) -> list[PubMedArticle]:
        term = query
        if mesh_terms:
            mesh_parts = " AND ".join(f"{t}[MeSH]" for t in mesh_terms)
            term = f"{query} AND {mesh_parts}"

        search_params: dict[str, str | int] = {
            "db": "pubmed",
            "retmode": "json",
            "retmax": max_results,
            "term": term,
        }
        search_data = await self._get(_ESEARCH_URL, search_params)

        result = search_data.get("esearchresult", {})
        if not isinstance(result, dict):
            return []
        id_list = result.get("idlist", [])
        if not isinstance(id_list, list) or not id_list:
            return []

        fetch_params: dict[str, str | int] = {
            "db": "pubmed",
            "rettype": "xml",
            "id": ",".join(str(pmid) for pmid in id_list),
        }
        resp = await self._get_raw(_EFETCH_URL, fetch_params)
        return self._parse_xml(resp)

    async def _get(self, url: str, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "PubMed rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("PubMed", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "PubMed timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("PubMed", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "PubMed",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    async def _get_raw(self, url: str, params: dict[str, str | int]) -> str:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "PubMed rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("PubMed", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.text
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "PubMed timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("PubMed", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "PubMed",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_xml(xml_text: str) -> list[PubMedArticle]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        articles: list[PubMedArticle] = []
        for article_el in root.findall(".//PubmedArticle"):
            citation = article_el.find("MedlineCitation")
            if citation is None:
                continue

            pmid_el = citation.find("PMID")
            pmid = pmid_el.text if pmid_el is not None and pmid_el.text else ""

            article = citation.find("Article")
            if article is None:
                continue

            title_el = article.find("ArticleTitle")
            title = title_el.text if title_el is not None and title_el.text else ""

            abstract_el = article.find(".//AbstractText")
            abstract = abstract_el.text if abstract_el is not None and abstract_el.text else ""

            authors: list[str] = []
            for author in article.findall(".//Author"):
                last = author.find("LastName")
                initials = author.find("Initials")
                if last is not None and last.text:
                    name = last.text
                    if initials is not None and initials.text:
                        name = f"{last.text} {initials.text}"
                    authors.append(name)

            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None and journal_el.text else ""

            year_el = citation.find(".//DateCompleted/Year")
            if year_el is None:
                year_el = citation.find(".//DateRevised/Year")
            try:
                year = int(year_el.text) if year_el is not None and year_el.text else 0
            except ValueError:
                year = 0

            doi = ""
            for aid in article.findall(".//ArticleId"):
                if aid.get("IdType") == "doi" and aid.text:
                    doi = aid.text
                    break

            mesh_terms: list[str] = []
            for mesh in citation.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

            pub_type_el = article.find(".//PublicationType")
            pub_type = pub_type_el.text if pub_type_el is not None and pub_type_el.text else ""

            articles.append(
                PubMedArticle(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    authors=tuple(authors),
                    journal=journal,
                    year=year,
                    doi=doi,
                    mesh_terms=tuple(mesh_terms),
                    publication_type=pub_type,
                )
            )

        return articles
