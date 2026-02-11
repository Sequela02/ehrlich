from __future__ import annotations

import hashlib
import json
import time


class ToolCache:
    _TTLS: dict[str, float] = {
        "compute_descriptors": float("inf"),
        "compute_fingerprint": float("inf"),
        "validate_smiles": float("inf"),
        "tanimoto_similarity": float("inf"),
        "search_literature": 86400,
        "explore_dataset": 604800,
        "search_bioactivity": 604800,
        "search_protein_targets": 604800,
        "search_compounds": 604800,
        "get_protein_annotation": 604800,
        "search_disease_targets": 604800,
        "search_pharmacology": 604800,
    }

    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float]] = {}

    def get(self, tool_name: str, args_hash: str) -> str | None:
        key = f"{tool_name}:{args_hash}"
        entry = self._store.get(key)
        if entry is None:
            return None
        result, expires_at = entry
        if expires_at != float("inf") and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return result

    def put(self, tool_name: str, args_hash: str, result: str) -> None:
        ttl = self._TTLS.get(tool_name)
        if ttl is None:
            return
        expires_at = float("inf") if ttl == float("inf") else time.monotonic() + ttl
        key = f"{tool_name}:{args_hash}"
        self._store[key] = (result, expires_at)

    @staticmethod
    def hash_args(args: dict[str, object]) -> str:
        raw = json.dumps(args, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()  # noqa: S324
