from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ehrlich.api.routes.investigation import _build_domain_registry, _build_registry
from ehrlich.api.sse import SSEEventType

router = APIRouter(tags=["stats"])

PHASE_COUNT = 6
DATA_SOURCE_COUNT = 13


class StatsResponse(BaseModel):
    tool_count: int
    domain_count: int
    phase_count: int
    data_source_count: int
    event_type_count: int


@router.get("/stats")
async def get_stats() -> StatsResponse:
    registry = _build_registry()
    domain_registry = _build_domain_registry()
    return StatsResponse(
        tool_count=len(registry.list_tools()),
        domain_count=len(domain_registry.all_configs()),
        phase_count=PHASE_COUNT,
        data_source_count=DATA_SOURCE_COUNT,
        event_type_count=len(SSEEventType),
    )
