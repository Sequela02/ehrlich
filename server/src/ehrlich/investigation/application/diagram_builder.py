from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ehrlich.investigation.domain.investigation import Investigation
    from ehrlich.investigation.infrastructure.mcp_bridge import MCPBridge

logger = logging.getLogger(__name__)


async def generate_diagram(mcp_bridge: MCPBridge, investigation: Investigation) -> str:
    """Generate an Excalidraw evidence synthesis diagram and return its URL."""
    elements = _build_excalidraw_elements(investigation)
    elements_json = json.dumps(elements)
    try:
        await mcp_bridge.call_tool("excalidraw:read_me", {})
        await mcp_bridge.call_tool("excalidraw:create_view", {"elements": elements_json})
        export_result = await mcp_bridge.call_tool(
            "excalidraw:export_to_excalidraw",
            {"json": json.dumps({"elements": elements, "appState": {}})},
        )
        data = json.loads(export_result)
        url: str = data.get("url", "")
        if url:
            logger.info("Diagram exported: %s", url)
        return url
    except Exception:
        logger.warning("Diagram generation failed", exc_info=True)
        return ""


def _build_excalidraw_elements(investigation: Investigation) -> list[dict[str, Any]]:
    """Build Excalidraw elements representing the investigation evidence map."""
    elements: list[dict[str, Any]] = []
    y_offset = 0

    # Title
    elements.append(
        {
            "type": "text",
            "x": 300,
            "y": y_offset,
            "width": 600,
            "height": 40,
            "text": f"Evidence Synthesis: {investigation.prompt[:80]}",
            "fontSize": 24,
            "fontFamily": 1,
            "textAlign": "center",
            "strokeColor": "#e2e8f0",
            "id": "title",
        }
    )
    y_offset += 80

    # Hypotheses
    status_colors = {
        "supported": "#166534",
        "refuted": "#991b1b",
        "revised": "#9a3412",
        "proposed": "#374151",
        "testing": "#1e40af",
        "rejected": "#7f1d1d",
    }
    hyp_positions: dict[str, tuple[int, int]] = {}
    for i, h in enumerate(investigation.hypotheses):
        x = 50 + (i % 3) * 350
        y = y_offset + (i // 3) * 160
        color = status_colors.get(h.status.value, "#374151")
        elements.append(
            {
                "type": "rectangle",
                "x": x,
                "y": y,
                "width": 300,
                "height": 120,
                "backgroundColor": color,
                "strokeColor": "#94a3b8",
                "roundness": {"type": 3},
                "id": f"hyp-{h.id}",
            }
        )
        label = f"{h.status.value.upper()}\n{h.statement[:60]}"
        if h.confidence > 0:
            label += f"\nConf: {h.confidence:.0%}"
        elements.append(
            {
                "type": "text",
                "x": x + 10,
                "y": y + 10,
                "width": 280,
                "height": 100,
                "text": label,
                "fontSize": 14,
                "fontFamily": 1,
                "strokeColor": "#e2e8f0",
                "id": f"hyp-label-{h.id}",
            }
        )
        hyp_positions[h.id] = (x + 150, y + 120)

    y_offset += ((len(investigation.hypotheses) + 2) // 3) * 160 + 40

    # Findings summary
    if investigation.findings:
        elements.append(
            {
                "type": "text",
                "x": 50,
                "y": y_offset,
                "width": 400,
                "height": 30,
                "text": f"Findings: {len(investigation.findings)} recorded",
                "fontSize": 18,
                "fontFamily": 1,
                "strokeColor": "#94a3b8",
                "id": "findings-header",
            }
        )
        y_offset += 50
        for j, f in enumerate(investigation.findings[:12]):
            elements.append(
                {
                    "type": "text",
                    "x": 60,
                    "y": y_offset + j * 25,
                    "width": 900,
                    "height": 20,
                    "text": f"[{f.evidence_type}] {f.title[:90]}",
                    "fontSize": 12,
                    "fontFamily": 3,
                    "strokeColor": "#94a3b8",
                    "id": f"finding-{j}",
                }
            )

    return elements
