import asyncio
import logging
import os

import httpx

from ehrlich.impact.domain.entities import DataPoint, EconomicSeries
from ehrlich.impact.domain.repository import EconomicDataRepository
from ehrlich.kernel.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0

# Common Banxico series IDs for search
_KNOWN_SERIES: dict[str, str] = {
    "tipo de cambio": "SF60653",
    "tipo_de_cambio": "SF60653",
    "exchange rate": "SF60653",
    "inflacion": "SP1",
    "inflation": "SP1",
    "tasa de interes": "SF61745",
    "tasa_de_interes": "SF61745",
    "interest rate": "SF61745",
    "reservas": "SF290383",
    "reserves": "SF290383",
}


class BanxicoClient(EconomicDataRepository):
    def __init__(self, api_token: str | None = None) -> None:
        self._token = api_token or os.environ.get("BANXICO_API_TOKEN", "")
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search_series(self, query: str, limit: int = 10) -> list[EconomicSeries]:
        if not self._token:
            return []
        # Resolve known keyword -> series ID; fallback to raw query as series ID
        series_id = _KNOWN_SERIES.get(query.lower().strip(), query.strip())
        series = await self.get_series(series_id)
        return [series] if series else []

    async def get_series(
        self, series_id: str, start: str | None = None, end: str | None = None
    ) -> EconomicSeries | None:
        if not self._token:
            return None
        start_date = start or "2000-01-01"
        end_date = end or "2024-12-31"
        url = f"{_BASE_URL}/{series_id}/datos/{start_date}/{end_date}"
        data = await self._get(url, {"token": self._token})

        bmx = data.get("bmx", {})
        if not isinstance(bmx, dict):
            return None
        series_list = bmx.get("series", [])
        if not isinstance(series_list, list) or not series_list:
            return None

        first = series_list[0]
        if not isinstance(first, dict):
            return None

        datos = first.get("datos", [])
        points: list[DataPoint] = []
        if isinstance(datos, list):
            for d in datos:
                if not isinstance(d, dict):
                    continue
                fecha = str(d.get("fecha", ""))
                raw_val = str(d.get("dato", "")).replace(",", ".")
                if raw_val in ("N/E", ""):
                    continue
                try:
                    value = float(raw_val)
                except (ValueError, TypeError):
                    continue
                points.append(DataPoint(date=fecha, value=value))

        title = str(first.get("titulo", series_id))
        return EconomicSeries(
            series_id=series_id,
            title=title,
            values=tuple(points),
            source="banxico",
            unit="",
            frequency="",
        )

    async def _get(self, url: str, params: dict[str, str]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(url, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "Banxico rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError("Banxico", "Rate limit exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "Banxico timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError("Banxico", f"HTTP {e.response.status_code}") from e
        raise ExternalServiceError(
            "Banxico",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )
