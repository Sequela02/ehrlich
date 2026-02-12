import asyncio
import logging

import httpx

from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.sports.domain.entities import ClinicalTrial
from ehrlich.sports.domain.repository import ClinicalTrialRepository

logger = logging.getLogger(__name__)

_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
_TIMEOUT = 20.0
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


class ClinicalTrialsClient(ClinicalTrialRepository):
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def search(
        self, condition: str, intervention: str = "", max_results: int = 10
    ) -> list[ClinicalTrial]:
        params: dict[str, str | int] = {
            "query.cond": condition,
            "pageSize": min(max_results, 50),
            "format": "json",
        }
        if intervention:
            params["query.intr"] = intervention

        data = await self._get(params)
        studies_raw = data.get("studies", [])
        studies = studies_raw if isinstance(studies_raw, list) else []
        return [self._parse_study(s) for s in studies[:max_results] if s]

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = await self._client.get(_BASE_URL, params=params)
                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2**attempt)
                    logger.warning(
                        "ClinicalTrials.gov rate limited (attempt %d/%d), retrying in %.1fs",
                        attempt + 1,
                        _MAX_RETRIES,
                        delay,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise ExternalServiceError(
                        "ClinicalTrials.gov", "Rate limit exceeded"
                    )
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except httpx.TimeoutException as e:
                last_error = e
                delay = _BASE_DELAY * (2**attempt)
                logger.warning(
                    "ClinicalTrials.gov timeout (attempt %d/%d), retrying in %.1fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    delay,
                )
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(delay)
                    continue
            except httpx.HTTPStatusError as e:
                raise ExternalServiceError(
                    "ClinicalTrials.gov", f"HTTP {e.response.status_code}"
                ) from e
        raise ExternalServiceError(
            "ClinicalTrials.gov",
            f"Request failed after {_MAX_RETRIES} attempts: {last_error}",
        )

    @staticmethod
    def _parse_study(study: dict[str, object]) -> ClinicalTrial:
        proto = study.get("protocolSection", {})
        if not isinstance(proto, dict):
            proto = {}

        ident = proto.get("identificationModule", {})
        if not isinstance(ident, dict):
            ident = {}

        design = proto.get("designModule", {})
        if not isinstance(design, dict):
            design = {}

        status_mod = proto.get("statusModule", {})
        if not isinstance(status_mod, dict):
            status_mod = {}

        arms = proto.get("armsInterventionsModule", {})
        if not isinstance(arms, dict):
            arms = {}

        outcomes_mod = proto.get("outcomesModule", {})
        if not isinstance(outcomes_mod, dict):
            outcomes_mod = {}

        conditions_mod = proto.get("conditionsModule", {})
        if not isinstance(conditions_mod, dict):
            conditions_mod = {}

        enrollment_info = design.get("enrollmentInfo", {})
        if not isinstance(enrollment_info, dict):
            enrollment_info = {}

        phases_raw = design.get("phases", [])
        phases = phases_raw if isinstance(phases_raw, list) else []

        interventions_raw = arms.get("interventions", [])
        interventions = interventions_raw if isinstance(interventions_raw, list) else []

        primary_raw = outcomes_mod.get("primaryOutcomes", [])
        primary_outcomes = primary_raw if isinstance(primary_raw, list) else []

        conditions_raw = conditions_mod.get("conditions", [])
        conditions = conditions_raw if isinstance(conditions_raw, list) else []

        start_raw = status_mod.get("startDateStruct", {})
        start_struct = start_raw if isinstance(start_raw, dict) else {}

        try:
            enrollment = int(enrollment_info.get("count", 0))
        except (ValueError, TypeError):
            enrollment = 0

        return ClinicalTrial(
            nct_id=str(ident.get("nctId", "")),
            title=str(ident.get("briefTitle", ""))[:200],
            status=str(status_mod.get("overallStatus", "")),
            phase=", ".join(str(p) for p in phases) if phases else "N/A",
            enrollment=enrollment,
            conditions=tuple(str(c) for c in conditions),
            interventions=tuple(
                str(i.get("name", "")) if isinstance(i, dict) else str(i)
                for i in interventions
            ),
            primary_outcomes=tuple(
                str(o.get("measure", "")) if isinstance(o, dict) else str(o)
                for o in primary_outcomes
            ),
            study_type=str(design.get("studyType", "")),
            start_date=str(start_struct.get("date", "")),
        )
