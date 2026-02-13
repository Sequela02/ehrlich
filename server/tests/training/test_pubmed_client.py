from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.training.infrastructure.pubmed_client import PubMedClient

_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


@pytest.fixture()
def client() -> PubMedClient:
    return PubMedClient()


_ESEARCH_RESPONSE = {"esearchresult": {"idlist": ["12345678"]}}

_EFETCH_XML = """\
<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal><Title>J Sports Med</Title></Journal>
        <ArticleTitle>HIIT and VO2max</ArticleTitle>
        <Abstract><AbstractText>Study abstract text.</AbstractText></Abstract>
        <AuthorList>
          <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
        </AuthorList>
        <ArticleIdList><ArticleId IdType="doi">10.1234/test</ArticleId></ArticleIdList>
        <PublicationTypeList>
          <PublicationType>Journal Article</PublicationType>
        </PublicationTypeList>
      </Article>
      <DateCompleted><Year>2024</Year></DateCompleted>
      <MeshHeadingList>
        <MeshHeading><DescriptorName>Exercise</DescriptorName></MeshHeading>
      </MeshHeadingList>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class TestSearch:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_returns_articles(self, client: PubMedClient) -> None:
        respx.get(_ESEARCH_URL).mock(return_value=Response(200, json=_ESEARCH_RESPONSE))
        respx.get(_EFETCH_URL).mock(return_value=Response(200, text=_EFETCH_XML))

        articles = await client.search("HIIT VO2max")
        assert len(articles) == 1
        a = articles[0]
        assert a.pmid == "12345678"
        assert a.title == "HIIT and VO2max"
        assert a.abstract == "Study abstract text."
        assert a.authors == ("Smith J",)
        assert a.journal == "J Sports Med"
        assert a.year == 2024
        assert a.doi == "10.1234/test"
        assert a.mesh_terms == ("Exercise",)
        assert a.publication_type == "Journal Article"

    @respx.mock
    @pytest.mark.asyncio()
    async def test_empty_results(self, client: PubMedClient) -> None:
        respx.get(_ESEARCH_URL).mock(
            return_value=Response(200, json={"esearchresult": {"idlist": []}})
        )
        articles = await client.search("nonexistent query")
        assert articles == []

    @respx.mock
    @pytest.mark.asyncio()
    async def test_with_mesh_terms(self, client: PubMedClient) -> None:
        route = respx.get(_ESEARCH_URL).mock(
            return_value=Response(200, json={"esearchresult": {"idlist": []}})
        )
        await client.search("HIIT", mesh_terms=["Resistance Training", "Muscle Strength"])
        request = route.calls[0].request
        term = str(request.url.params.get("term", ""))
        assert "Resistance Training[MeSH]" in term
        assert "Muscle Strength[MeSH]" in term

    @respx.mock
    @pytest.mark.asyncio()
    async def test_http_error(self, client: PubMedClient) -> None:
        respx.get(_ESEARCH_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="PubMed"):
            await client.search("error test")


class TestRetry:
    @respx.mock
    @pytest.mark.asyncio()
    async def test_rate_limit_retry(self, client: PubMedClient) -> None:
        route = respx.get(_ESEARCH_URL)
        route.side_effect = [
            Response(429),
            Response(200, json={"esearchresult": {"idlist": []}}),
        ]
        articles = await client.search("retry test")
        assert articles == []
