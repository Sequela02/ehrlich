from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_VINA_AVAILABLE = False
try:
    import meeko as _meeko  # noqa: F401
    import vina as _vina  # noqa: F401

    _VINA_AVAILABLE = True
except ImportError:
    pass


def interpret_energy(energy: float) -> str:
    if energy <= -10.0:
        return "excellent"
    if energy <= -8.0:
        return "strong"
    if energy <= -6.0:
        return "moderate"
    return "weak"


class VinaAdapter:
    @staticmethod
    def is_available() -> bool:
        return _VINA_AVAILABLE

    async def dock(
        self,
        mol_block: str,
        target_pdbqt: str,
        center: tuple[float, float, float],
        box_size: float,
    ) -> dict[str, float]:
        if not _VINA_AVAILABLE:
            raise ImportError("Vina/Meeko not installed. Install with: uv sync --extra docking")
        raise NotImplementedError("Vina docking pipeline not yet implemented")
