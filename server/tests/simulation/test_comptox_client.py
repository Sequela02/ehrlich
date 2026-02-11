from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.simulation.infrastructure.comptox_client import CompToxClient


@pytest.fixture
def client() -> CompToxClient:
    return CompToxClient(api_key="test-key-123")


@pytest.fixture
def client_no_key() -> CompToxClient:
    return CompToxClient(api_key="")


class TestFetch:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_profile(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/bisphenol%20a").mock(
            return_value=Response(
                200,
                json=[{"dtxsid": "DTXSID7020182", "casrn": "80-05-7"}],
            )
        )
        respx.get("https://api-ccte.epa.gov/hazard/search/by-dtxsid/DTXSID7020182").mock(
            return_value=Response(
                200,
                json=[
                    {
                        "casrn": "80-05-7",
                        "molecularWeight": 228.29,
                        "endpointCategory": "acute oral",
                        "toxvalNumeric": "3250",
                        "toxvalType": "LD50",
                    },
                    {
                        "endpointCategory": "acute aquatic",
                        "toxvalNumeric": "4.7",
                        "toxvalType": "LC50",
                    },
                    {
                        "endpointCategory": "bioconcentration",
                        "toxvalNumeric": "70.8",
                        "toxvalType": "BCF",
                    },
                    {
                        "endpointCategory": "developmental",
                        "toxvalType": "positive",
                    },
                    {
                        "endpointCategory": "mutagenicity",
                        "toxvalType": "negative",
                    },
                ],
            )
        )

        profile = await client.fetch("bisphenol a")
        assert profile is not None
        assert profile.dtxsid == "DTXSID7020182"
        assert profile.name == "bisphenol a"
        assert profile.casrn == "80-05-7"
        assert profile.molecular_weight == 228.29
        assert profile.oral_rat_ld50 == 3250.0
        assert profile.lc50_fish == 4.7
        assert profile.bioconcentration_factor == 70.8
        assert profile.developmental_toxicity is True
        assert profile.mutagenicity is False
        assert profile.source == "epa_comptox"

    @respx.mock
    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self, client_no_key: CompToxClient) -> None:
        profile = await client_no_key.fetch("bisphenol a")
        assert profile is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_chemical_not_found(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/zzzzz").mock(
            return_value=Response(404)
        )
        profile = await client.fetch("zzzzz")
        assert profile is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_hazard_not_found(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/test").mock(
            return_value=Response(200, json=[{"dtxsid": "DTXSID000"}])
        )
        respx.get("https://api-ccte.epa.gov/hazard/search/by-dtxsid/DTXSID000").mock(
            return_value=Response(404)
        )
        profile = await client.fetch("test")
        assert profile is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_raises(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/bad").mock(
            return_value=Response(500)
        )
        with pytest.raises(ExternalServiceError, match="EPA CompTox"):
            await client.fetch("bad")


class TestResolveRetry:
    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: CompToxClient) -> None:
        route = respx.get("https://api-ccte.epa.gov/chemical/search/by-name/retry")
        route.side_effect = [
            Response(429),
            Response(200, json=[{"dtxsid": "DTXSID001"}]),
        ]
        respx.get("https://api-ccte.epa.gov/hazard/search/by-dtxsid/DTXSID001").mock(
            return_value=Response(
                200, json=[{"endpointCategory": "acute oral", "toxvalNumeric": "100"}]
            )
        )
        profile = await client.fetch("retry")
        assert profile is not None
        assert profile.dtxsid == "DTXSID001"

    @respx.mock
    @pytest.mark.asyncio
    async def test_hazard_rate_limit_retry(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/test2").mock(
            return_value=Response(200, json=[{"dtxsid": "DTXSID002"}])
        )
        route = respx.get("https://api-ccte.epa.gov/hazard/search/by-dtxsid/DTXSID002")
        route.side_effect = [
            Response(429),
            Response(200, json=[{"endpointCategory": "mutagenicity", "toxvalType": "positive"}]),
        ]
        profile = await client.fetch("test2")
        assert profile is not None
        assert profile.mutagenicity is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_dict_response(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/single").mock(
            return_value=Response(200, json={"dtxsid": "DTXSID003"})
        )
        respx.get("https://api-ccte.epa.gov/hazard/search/by-dtxsid/DTXSID003").mock(
            return_value=Response(200, json=[])
        )
        profile = await client.fetch("single")
        assert profile is not None
        assert profile.dtxsid == "DTXSID003"

    @respx.mock
    @pytest.mark.asyncio
    async def test_resolve_empty_list(self, client: CompToxClient) -> None:
        respx.get("https://api-ccte.epa.gov/chemical/search/by-name/empty").mock(
            return_value=Response(200, json=[])
        )
        profile = await client.fetch("empty")
        assert profile is None


class TestParseHazard:
    def test_empty_records(self) -> None:
        profile = CompToxClient._parse_hazard([], "DTX000", "test")
        assert profile.dtxsid == "DTX000"
        assert profile.oral_rat_ld50 is None
        assert profile.mutagenicity is None

    def test_dict_record(self) -> None:
        data = {
            "casrn": "123-45-6",
            "molecularWeight": 100.0,
            "endpointCategory": "acute oral",
            "toxvalNumeric": "500",
        }
        profile = CompToxClient._parse_hazard(data, "DTX001", "compound")
        assert profile.casrn == "123-45-6"
        assert profile.molecular_weight == 100.0
        assert profile.oral_rat_ld50 == 500.0
