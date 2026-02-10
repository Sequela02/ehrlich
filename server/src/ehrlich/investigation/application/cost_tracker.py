from dataclasses import dataclass, field


@dataclass
class CostTracker:
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    _cost_per_input_token: float = field(default=0.000003, repr=False)
    _cost_per_output_token: float = field(default=0.000015, repr=False)

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def add_tool_call(self) -> None:
        self.tool_calls += 1

    @property
    def total_cost(self) -> float:
        return (
            self.input_tokens * self._cost_per_input_token
            + self.output_tokens * self._cost_per_output_token
        )

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict[str, object]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "tool_calls": self.tool_calls,
            "total_cost_usd": round(self.total_cost, 6),
        }
