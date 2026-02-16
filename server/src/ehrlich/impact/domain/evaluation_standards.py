"""Impact-specific evaluation standards.

CONEVAL MIR (Matriz de Indicadores para Resultados) levels
and CREMAA quality criteria for Mexican social programs.
"""

from __future__ import annotations

CONEVAL_MIR_LEVELS: dict[str, str] = {
    "fin": "Long-term societal goal the program contributes to",
    "proposito": "Direct outcome expected for the target population",
    "componente": "Goods or services delivered by the program",
    "actividad": "Key activities required to produce components",
}

CREMAA_CRITERIA: dict[str, str] = {
    "claridad": "Indicator is clear and unambiguous",
    "relevancia": "Indicator is relevant to the program objective",
    "economia": "Data collection is cost-effective",
    "monitoreable": "Indicator can be tracked systematically",
    "adecuado": "Indicator is appropriate for the level it measures",
    "aportacion_marginal": "Indicator adds unique information not captured elsewhere",
}
