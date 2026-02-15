"""Tests for Mexico API clients (INEGI, Banxico, datos.gob.mx)."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from ehrlich.impact.infrastructure.banxico_client import BanxicoClient
from ehrlich.impact.infrastructure.datosgob_client import DatosGobClient
from ehrlich.impact.infrastructure.inegi_client import INEGIClient
from ehrlich.kernel.exceptions import ExternalServiceError

# --- INEGI ---

_INEGI_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/493911/es/0700/true/bib/test_token"
_INEGI_RESPONSE = {
    "Series": [
        {
            "LASTUPDATE": "PIB Total",
            "UNIT": "Millones de pesos",
            "FREQ": "Quarterly",
            "OBSERVATIONS": [
                {"TIME_PERIOD": "2023-Q1", "OBS_VALUE": "25000000.0"},
                {"TIME_PERIOD": "2023-Q2", "OBS_VALUE": "25500000.0"},
            ],
        }
    ]
}


class TestINEGIClient:
    @pytest.fixture
    def client(self) -> INEGIClient:
        return INEGIClient(api_token="test_token")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_series(self, client: INEGIClient) -> None:
        respx.get(_INEGI_URL).mock(return_value=Response(200, json=_INEGI_RESPONSE))
        result = await client.get_series("493911")
        assert result is not None
        assert result.series_id == "493911"
        assert result.source == "inegi"
        assert result.title == "PIB Total"
        assert result.unit == "Millones de pesos"
        assert result.frequency == "Quarterly"
        assert len(result.values) == 2
        assert result.values[0].date == "2023-Q1"
        assert result.values[0].value == 25000000.0

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_series_known_keyword(self, client: INEGIClient) -> None:
        respx.get(_INEGI_URL).mock(return_value=Response(200, json=_INEGI_RESPONSE))
        results = await client.search_series("pib")
        assert len(results) == 1
        assert results[0].source == "inegi"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_series_with_date_filter(self, client: INEGIClient) -> None:
        respx.get(_INEGI_URL).mock(return_value=Response(200, json=_INEGI_RESPONSE))
        result = await client.get_series("493911", start="2023-Q2", end="2023-Q4")
        assert result is not None
        assert len(result.values) == 1
        assert result.values[0].date == "2023-Q2"

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_series_response(self, client: INEGIClient) -> None:
        respx.get(_INEGI_URL).mock(return_value=Response(200, json={"Series": []}))
        result = await client.get_series("493911")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_invalid_obs_value_skipped(self, client: INEGIClient) -> None:
        response = {
            "Series": [
                {
                    "LASTUPDATE": "Test",
                    "UNIT": "",
                    "FREQ": "",
                    "OBSERVATIONS": [
                        {"TIME_PERIOD": "2023-Q1", "OBS_VALUE": "N/A"},
                        {"TIME_PERIOD": "2023-Q2", "OBS_VALUE": "1000.0"},
                    ],
                }
            ]
        }
        respx.get(_INEGI_URL).mock(return_value=Response(200, json=response))
        result = await client.get_series("493911")
        assert result is not None
        assert len(result.values) == 1

    @pytest.mark.asyncio
    async def test_no_token_returns_empty(self) -> None:
        client = INEGIClient(api_token="")
        results = await client.search_series("pib")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_token_get_series_returns_none(self) -> None:
        client = INEGIClient(api_token="")
        result = await client.get_series("493911")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: INEGIClient) -> None:
        respx.get(_INEGI_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="INEGI"):
            await client.get_series("493911")

    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: INEGIClient) -> None:
        route = respx.get(_INEGI_URL)
        route.side_effect = [
            Response(429),
            Response(200, json=_INEGI_RESPONSE),
        ]
        result = await client.get_series("493911")
        assert result is not None


# --- Banxico ---

_BANXICO_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF60653/datos"
_BANXICO_RESPONSE = {
    "bmx": {
        "series": [
            {
                "titulo": "Tipo de cambio USD/MXN",
                "datos": [
                    {"fecha": "2024-01-02", "dato": "17.12"},
                    {"fecha": "2024-01-03", "dato": "17.05"},
                    {"fecha": "2024-01-04", "dato": "N/E"},
                ],
            }
        ]
    }
}


class TestBanxicoClient:
    @pytest.fixture
    def client(self) -> BanxicoClient:
        return BanxicoClient(api_token="test_token")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_series(self, client: BanxicoClient) -> None:
        respx.get(url__startswith=_BANXICO_BASE).mock(
            return_value=Response(200, json=_BANXICO_RESPONSE)
        )
        result = await client.get_series("SF60653")
        assert result is not None
        assert result.series_id == "SF60653"
        assert result.source == "banxico"
        assert result.title == "Tipo de cambio USD/MXN"
        # N/E dato is skipped
        assert len(result.values) == 2
        assert result.values[0].date == "2024-01-02"
        assert result.values[0].value == 17.12

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_series_known_keyword(self, client: BanxicoClient) -> None:
        respx.get(url__startswith=_BANXICO_BASE).mock(
            return_value=Response(200, json=_BANXICO_RESPONSE)
        )
        results = await client.search_series("tipo de cambio")
        assert len(results) == 1
        assert results[0].source == "banxico"

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_series_raw_id(self, client: BanxicoClient) -> None:
        respx.get(url__startswith=_BANXICO_BASE).mock(
            return_value=Response(200, json=_BANXICO_RESPONSE)
        )
        results = await client.search_series("SF60653")
        assert len(results) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_series_response(self, client: BanxicoClient) -> None:
        respx.get(url__startswith=_BANXICO_BASE).mock(
            return_value=Response(200, json={"bmx": {"series": []}})
        )
        result = await client.get_series("SF60653")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_comma_decimal_handling(self, client: BanxicoClient) -> None:
        response = {
            "bmx": {
                "series": [
                    {
                        "titulo": "Test",
                        "datos": [{"fecha": "2024-01-01", "dato": "17,500"}],
                    }
                ]
            }
        }
        respx.get(url__startswith=_BANXICO_BASE).mock(return_value=Response(200, json=response))
        result = await client.get_series("SF60653")
        assert result is not None
        assert result.values[0].value == 17.5

    @pytest.mark.asyncio
    async def test_no_token_returns_empty(self) -> None:
        client = BanxicoClient(api_token="")
        results = await client.search_series("tipo de cambio")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_token_get_series_returns_none(self) -> None:
        client = BanxicoClient(api_token="")
        result = await client.get_series("SF60653")
        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: BanxicoClient) -> None:
        respx.get(url__startswith=_BANXICO_BASE).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="Banxico"):
            await client.get_series("SF60653")

    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: BanxicoClient) -> None:
        route = respx.get(url__startswith=_BANXICO_BASE)
        route.side_effect = [
            Response(429),
            Response(200, json=_BANXICO_RESPONSE),
        ]
        result = await client.get_series("SF60653")
        assert result is not None


# --- datos.gob.mx ---

_DATOSGOB_URL = "https://datos.gob.mx/busca/api/3/action/package_search"
_DATOSGOB_RESPONSE = {
    "result": {
        "results": [
            {
                "id": "mx-ds-001",
                "title": "Programas Sociales 2023",
                "organization": {"title": "SEDESOL"},
                "notes": "Datos de programas sociales federales",
                "tags": [{"name": "social"}, {"name": "beneficiarios"}],
                "resources": [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}],
                "metadata_modified": "2023-12-15",
            }
        ]
    }
}


class TestDatosGobClient:
    @pytest.fixture
    def client(self) -> DatosGobClient:
        return DatosGobClient()

    @respx.mock
    @pytest.mark.asyncio
    async def test_search_datasets(self, client: DatosGobClient) -> None:
        respx.get(_DATOSGOB_URL).mock(return_value=Response(200, json=_DATOSGOB_RESPONSE))
        results = await client.search_datasets("programa social")
        assert len(results) == 1
        assert results[0].dataset_id == "mx-ds-001"
        assert results[0].title == "Programas Sociales 2023"
        assert results[0].organization == "SEDESOL"
        assert results[0].tags == ("social", "beneficiarios")
        assert results[0].resource_count == 3
        assert results[0].modified == "2023-12-15"

    @respx.mock
    @pytest.mark.asyncio
    async def test_description_truncated(self, client: DatosGobClient) -> None:
        long_notes = "x" * 600
        response = {
            "result": {
                "results": [
                    {
                        "id": "ds-long",
                        "title": "Test",
                        "organization": {},
                        "notes": long_notes,
                        "tags": [],
                        "resources": [],
                        "metadata_modified": "",
                    }
                ]
            }
        }
        respx.get(_DATOSGOB_URL).mock(return_value=Response(200, json=response))
        results = await client.search_datasets("test")
        assert len(results[0].description) == 500

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_organization_filter(self, client: DatosGobClient) -> None:
        respx.get(_DATOSGOB_URL).mock(return_value=Response(200, json=_DATOSGOB_RESPONSE))
        results = await client.search_datasets("salud", organization="ssa")
        assert len(results) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self, client: DatosGobClient) -> None:
        respx.get(_DATOSGOB_URL).mock(
            return_value=Response(200, json={"result": {"results": []}})
        )
        results = await client.search_datasets("nonexistent")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_malformed_result(self, client: DatosGobClient) -> None:
        respx.get(_DATOSGOB_URL).mock(return_value=Response(200, json={"result": "bad"}))
        results = await client.search_datasets("test")
        assert results == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error(self, client: DatosGobClient) -> None:
        respx.get(_DATOSGOB_URL).mock(return_value=Response(500))
        with pytest.raises(ExternalServiceError, match="datos.gob.mx"):
            await client.search_datasets("test")

    @respx.mock
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client: DatosGobClient) -> None:
        route = respx.get(_DATOSGOB_URL)
        route.side_effect = [
            Response(429),
            Response(200, json=_DATOSGOB_RESPONSE),
        ]
        results = await client.search_datasets("programa")
        assert len(results) == 1
