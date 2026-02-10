from ehrlich.investigation.domain.investigation import Investigation, InvestigationStatus


class Orchestrator:
    async def run(self, investigation: Investigation) -> Investigation:
        investigation.status = InvestigationStatus.RUNNING
        # TODO: Implement agentic loop (while/stop_reason + tool dispatch + SSE emit)
        investigation.status = InvestigationStatus.COMPLETED
        return investigation
