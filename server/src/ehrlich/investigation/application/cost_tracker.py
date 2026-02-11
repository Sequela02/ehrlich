from __future__ import annotations

from dataclasses import dataclass, field

# Pricing per million tokens (USD)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_M, output_per_M)
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
}

_DEFAULT_INPUT_RATE = 15.0
_DEFAULT_OUTPUT_RATE = 75.0


@dataclass
class _ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0


@dataclass
class CostTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    _by_model: dict[str, _ModelUsage] = field(default_factory=dict, repr=False)

    def add_usage(self, input_tokens: int, output_tokens: int, model: str = "") -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        if model:
            usage = self._by_model.setdefault(model, _ModelUsage())
            usage.input_tokens += input_tokens
            usage.output_tokens += output_tokens
            usage.calls += 1

    def add_tool_call(self) -> None:
        self.tool_calls += 1

    @property
    def total_cost(self) -> float:
        if not self._by_model:
            # Fallback: assume Opus pricing for backwards compatibility
            return (
                self.input_tokens * _DEFAULT_INPUT_RATE / 1_000_000
                + self.output_tokens * _DEFAULT_OUTPUT_RATE / 1_000_000
            )
        cost = 0.0
        for model, usage in self._by_model.items():
            input_rate, output_rate = _MODEL_PRICING.get(
                model, (_DEFAULT_INPUT_RATE, _DEFAULT_OUTPUT_RATE)
            )
            cost += usage.input_tokens * input_rate / 1_000_000
            cost += usage.output_tokens * output_rate / 1_000_000
        return cost

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "tool_calls": self.tool_calls,
            "total_cost_usd": round(self.total_cost, 6),
        }
        if self._by_model:
            breakdown: dict[str, object] = {}
            for model, usage in self._by_model.items():
                input_rate, output_rate = _MODEL_PRICING.get(
                    model, (_DEFAULT_INPUT_RATE, _DEFAULT_OUTPUT_RATE)
                )
                model_cost = (
                    usage.input_tokens * input_rate / 1_000_000
                    + usage.output_tokens * output_rate / 1_000_000
                )
                breakdown[model] = {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "calls": usage.calls,
                    "cost_usd": round(model_cost, 6),
                }
            result["by_model"] = breakdown
        return result
