from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_CHEMPROP_AVAILABLE = False
try:
    import chemprop as _chemprop  # noqa: F401

    _CHEMPROP_AVAILABLE = True
except ImportError:
    pass


class ChempropAdapter:
    @staticmethod
    def is_available() -> bool:
        return _CHEMPROP_AVAILABLE

    async def train(self, smiles_list: list[str], activities: list[float]) -> object:
        if not _CHEMPROP_AVAILABLE:
            raise ImportError("Chemprop not installed. Install with: uv sync --extra deeplearning")
        raise NotImplementedError("Chemprop training not yet implemented")

    async def predict(self, smiles_list: list[str], model: object) -> list[float]:
        if not _CHEMPROP_AVAILABLE:
            raise ImportError("Chemprop not installed. Install with: uv sync --extra deeplearning")
        raise NotImplementedError("Chemprop prediction not yet implemented")
