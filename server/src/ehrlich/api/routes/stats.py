from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ehrlich.api.sse import SSEEventType
from ehrlich.investigation.application.registry_factory import (
    build_domain_registry,
    build_tool_registry,
)

router = APIRouter(tags=["stats"])

PHASE_COUNT = 6
DATA_SOURCE_COUNT = 19


class StatsResponse(BaseModel):
    tool_count: int
    domain_count: int
    phase_count: int
    data_source_count: int
    event_type_count: int


@router.get("/stats")
async def get_stats() -> StatsResponse:
    registry = build_tool_registry()
    domain_registry = build_domain_registry()
    return StatsResponse(
        tool_count=len(registry.list_tools()),
        domain_count=len(domain_registry.all_configs()),
        phase_count=PHASE_COUNT,
        data_source_count=DATA_SOURCE_COUNT,
        event_type_count=len(SSEEventType),
    )
