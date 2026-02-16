from __future__ import annotations

from dataclasses import dataclass, field

# Pricing per million tokens (USD)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_M, output_per_M)
    "claude-opus-4-6": (5.0, 25.0),
    "claude-opus-4-5-20251101": (5.0, 25.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}

_DEFAULT_INPUT_RATE = 5.0
_DEFAULT_OUTPUT_RATE = 25.0

# Short display labels for model IDs
_MODEL_DISPLAY: dict[str, str] = {
    "claude-opus-4-6": "Opus 4.6",
    "claude-opus-4-5-20251101": "Opus 4.5",
    "claude-sonnet-4-5-20250929": "Sonnet 4.5",
    "claude-haiku-4-5-20251001": "Haiku 4.5",
}


@dataclass
class _RoleUsage:
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    calls: int = 0


@dataclass
class CostTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    tool_calls: int = 0
    _by_role: dict[str, _RoleUsage] = field(default_factory=dict, repr=False)

    def add_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "",
        *,
        role: str = "",
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cache_read_tokens += cache_read_tokens
        self.cache_write_tokens += cache_write_tokens
        key = role or model
        if key:
            usage = self._by_role.setdefault(key, _RoleUsage(model=model))
            if not usage.model:
                usage.model = model
            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.cache_read_tokens += cache_read_tokens
            usage.cache_write_tokens += cache_write_tokens
            usage.calls += 1

    def add_tool_call(self) -> None:
        self.tool_calls += 1

    @property
    def total_cost(self) -> float:
        if not self._by_role:
            return (
                self.input_tokens * _DEFAULT_INPUT_RATE / 1_000_000
                + self.cache_write_tokens * _DEFAULT_INPUT_RATE * 1.25 / 1_000_000
                + self.cache_read_tokens * _DEFAULT_INPUT_RATE * 0.1 / 1_000_000
                + self.output_tokens * _DEFAULT_OUTPUT_RATE / 1_000_000
            )
        cost = 0.0
        for usage in self._by_role.values():
            input_rate, output_rate = _MODEL_PRICING.get(
                usage.model, (_DEFAULT_INPUT_RATE, _DEFAULT_OUTPUT_RATE)
            )
            cost += usage.input_tokens * input_rate / 1_000_000
            cost += usage.cache_write_tokens * input_rate * 1.25 / 1_000_000
            cost += usage.cache_read_tokens * input_rate * 0.1 / 1_000_000
            cost += usage.output_tokens * output_rate / 1_000_000
        return cost

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "total_tokens": self.total_tokens,
            "tool_calls": self.tool_calls,
            "total_cost_usd": round(self.total_cost, 6),
        }
        if self._by_role:
            breakdown: dict[str, object] = {}
            for role, usage in self._by_role.items():
                input_rate, output_rate = _MODEL_PRICING.get(
                    usage.model, (_DEFAULT_INPUT_RATE, _DEFAULT_OUTPUT_RATE)
                )
                role_cost = (
                    usage.input_tokens * input_rate / 1_000_000
                    + usage.cache_write_tokens * input_rate * 1.25 / 1_000_000
                    + usage.cache_read_tokens * input_rate * 0.1 / 1_000_000
                    + usage.output_tokens * output_rate / 1_000_000
                )
                breakdown[role] = {
                    "model": usage.model,
                    "model_display": _MODEL_DISPLAY.get(usage.model, usage.model),
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cache_read_tokens": usage.cache_read_tokens,
                    "cache_write_tokens": usage.cache_write_tokens,
                    "calls": usage.calls,
                    "cost_usd": round(role_cost, 6),
                }
            result["by_role"] = breakdown
        return result
