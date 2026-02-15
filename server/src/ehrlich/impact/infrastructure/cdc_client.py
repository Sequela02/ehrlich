import asyncio
import logging
import xml.etree.ElementTree as ET

import httpx

from ehrlich.impact.domain.entities import HealthIndicator
from ehrlich.impact.domain.repository import HealthDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://wonder.cdc.gov/controller/datarequest"
_TIMEOUT = 30.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

_DATABASES = {
    "mortality": "D76",
    "natality": "D66",
    "infant_mortality": "D69",
}


class CDCWonderClient(HealthDataRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_indicators(
        self,
        indicator: str,
        country: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 10,
    ) -> list[HealthIndicator]:
        db_id = _DATABASES.get(indicator.lower(), indicator)
        xml_request = self._build_request(db_id, year_start, year_end)

        data = await self._post(f"{_BASE_URL}/{db_id}", xml_request)
        return self._parse_response(data, indicator, limit)

    def _build_request(
        self,
        db_id: str,
        year_start: int | None = None,
        year_end: int | None = None,
    ) -> str:
        params = [
            '<parameter><name>B_1</name><value>*All*</value></parameter>',
            '<parameter><name>B_2</name><value>*All*</value></parameter>',
            '<parameter><name>M_1</name><value>D76.M1</value></parameter>',
            '<parameter><name>O_V1_fmode</name><value>freg</value></parameter>',
            '<parameter><name>O_V2_fmode</name><value>freg</value></parameter>',
        ]
        if year_start:
            params.append(
                f'<parameter><name>V_D76.V1</name><value>{year_start}</value></parameter>'
            )
        if year_end:
            params.append(
                f'<parameter><name>V_D76.V1_end</name><value>{year_end}</value></parameter>'
            )

        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            "<request-parameters>"
            + "".join(params)
            + "</request-parameters>"
        )

    def _parse_response(
        self, xml_text: str, indicator: str, limit: int
    ) -> list[HealthIndicator]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("CDC WONDER returned invalid XML")
            return []

        results: list[HealthIndicator] = []
        for row in root.iter("r"):
            cells = list(row.iter("c"))
            if len(cells) < 3:
                continue

            year_text = cells[0].get("v", "") or cells[0].text or ""
            label = cells[0].get("l", "") or year_text
            value_text = cells[-1].get("v", "") or cells[-1].text or ""

            try:
                year = int(year_text[:4]) if year_text else 0
            except (ValueError, TypeError):
                year = 0

            try:
                value = float(value_text)
            except (ValueError, TypeError):
                continue

            results.append(
                HealthIndicator(
                    indicator_code=indicator,
                    indicator_name=label,
                    country="US",
                    year=year,
                    value=value,
                    unit="per 100,000",
                )
            )
            if len(results) >= limit:
                break
        return results

    async def _post(self, url: str, xml_body: str) -> str:
        last_error: Exception | None = None
        headers = {"Content-Type": "application/xml"}
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.post(url, content=xml_body, headers=headers)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "CDC WONDER rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("CDC WONDER", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.text
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "CDC WONDER timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "CDC WONDER", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "CDC WONDER",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )
