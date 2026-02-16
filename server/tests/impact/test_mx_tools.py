"""Tests for Mexico-specific Impact Evaluation tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from ehrlich.impact.domain.entities import DatasetMetadata, EconomicSeries
from ehrlich.impact.tools import (
    analyze_program_indicators,
    search_economic_indicators,
    search_open_data,
)

_INEGI_SERIES = EconomicSeries(
    series_id="493911",
    title="PIB Total",
    values=(),
    source="inegi",
    unit="Millones de pesos",
    frequency="Quarterly",
)

_BANXICO_SERIES = EconomicSeries(
    series_id="SF60653",
    title="Tipo de cambio USD/MXN",
    values=(),
    source="banxico",
    unit="",
    frequency="",
)

_MX_DATASET = DatasetMetadata(
    dataset_id="mx-ds-001",
    title="Programas Sociales 2023",
    organization="SEDESOL",
    description="Datos de programas sociales",
    tags=("social", "beneficiarios"),
    resource_count=3,
    modified="2023-12-15",
)


class TestSearchEconomicIndicatorsINEGI:
    @pytest.mark.asyncio
    async def test_inegi_source(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_inegi_data",
            new_callable=AsyncMock,
            return_value=[_INEGI_SERIES],
        ):
            result = json.loads(await search_economic_indicators("pib", source="inegi"))
            assert result["source"] == "INEGI"
            assert result["count"] == 1
            assert result["series"][0]["series_id"] == "493911"
            assert result["series"][0]["source"] == "inegi"
            assert result["series"][0]["unit"] == "Millones de pesos"
            assert result["series"][0]["frequency"] == "Quarterly"

    @pytest.mark.asyncio
    async def test_inegi_empty_results(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_inegi_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_economic_indicators("unknown", source="inegi"))
            assert result["source"] == "INEGI"
            assert result["count"] == 0
            assert result["series"] == []


class TestSearchEconomicIndicatorsBanxico:
    @pytest.mark.asyncio
    async def test_banxico_source(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_banxico_data",
            new_callable=AsyncMock,
            return_value=[_BANXICO_SERIES],
        ):
            result = json.loads(
                await search_economic_indicators("tipo de cambio", source="banxico")
            )
            assert result["source"] == "Banxico"
            assert result["count"] == 1
            assert result["series"][0]["series_id"] == "SF60653"
            assert result["series"][0]["source"] == "banxico"

    @pytest.mark.asyncio
    async def test_banxico_empty_results(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_banxico_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_economic_indicators("unknown", source="banxico"))
            assert result["source"] == "Banxico"
            assert result["count"] == 0


class TestSearchOpenDataDatosGob:
    @pytest.mark.asyncio
    async def test_datosgob_source(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_mexican_open_data",
            new_callable=AsyncMock,
            return_value=[_MX_DATASET],
        ):
            result = json.loads(await search_open_data("programa social", source="datosgob"))
            assert result["source"] == "datos.gob.mx"
            assert result["count"] == 1
            assert result["datasets"][0]["title"] == "Programas Sociales 2023"
            assert result["datasets"][0]["organization"] == "SEDESOL"
            assert result["datasets"][0]["tags"] == ["social", "beneficiarios"]
            assert result["datasets"][0]["resource_count"] == 3

    @pytest.mark.asyncio
    async def test_datosgob_empty_results(self) -> None:
        with patch(
            "ehrlich.impact.tools._service.search_mexican_open_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_open_data("nonexistent", source="datosgob"))
            assert result["source"] == "datos.gob.mx"
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_datagov_default_source(self) -> None:
        """Default source remains data.gov."""
        with patch(
            "ehrlich.impact.tools._service.search_open_data",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = json.loads(await search_open_data("poverty"))
            assert result["source"] == "data.gov"


class TestAnalyzeProgramIndicators:
    @pytest.mark.asyncio
    async def test_valid_proposito_level(self) -> None:
        result = json.loads(
            await analyze_program_indicators(
                indicator_name="Porcentaje de beneficiarios con mejora educativa",
                level="proposito",
            )
        )
        assert result["indicator_name"] == "Porcentaje de beneficiarios con mejora educativa"
        assert result["mir_level"] == "proposito"
        assert "cremaa_criteria" in result
        assert result["total_criteria"] == 6

    @pytest.mark.asyncio
    async def test_all_mir_levels(self) -> None:
        for level in ("fin", "proposito", "componente", "actividad"):
            result = json.loads(
                await analyze_program_indicators(indicator_name="Test indicator", level=level)
            )
            assert result["mir_level"] == level
            assert result["mir_level_description"] != f"Unknown MIR level: {level}"

    @pytest.mark.asyncio
    async def test_unknown_level_graceful(self) -> None:
        result = json.loads(
            await analyze_program_indicators(indicator_name="Test", level="unknown_level")
        )
        assert "Unknown MIR level" in result["mir_level_description"]

    @pytest.mark.asyncio
    async def test_cremaa_criteria_present(self) -> None:
        result = json.loads(
            await analyze_program_indicators(
                indicator_name="Cobertura del programa", level="componente"
            )
        )
        criteria = result["cremaa_criteria"]
        cremaa_keys = (
            "claridad",
            "relevancia",
            "economia",
            "monitoreable",
            "adecuado",
            "aportacion_marginal",
        )
        for key in cremaa_keys:
            assert key in criteria
            assert "description" in criteria[key]
            assert "status" in criteria[key]
            assert "guidance" in criteria[key]

    @pytest.mark.asyncio
    async def test_level_normalized_to_lowercase(self) -> None:
        result = json.loads(
            await analyze_program_indicators(indicator_name="Test", level="PROPOSITO")
        )
        assert result["mir_level"] == "proposito"
