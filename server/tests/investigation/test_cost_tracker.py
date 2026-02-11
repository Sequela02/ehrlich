from ehrlich.investigation.application.cost_tracker import CostTracker


class TestCostTracker:
    def test_initial_state(self) -> None:
        tracker = CostTracker()
        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0
        assert tracker.tool_calls == 0
        assert tracker.total_cost == 0.0
        assert tracker.total_tokens == 0

    def test_add_usage_without_model(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1000, 500)
        assert tracker.input_tokens == 1000
        assert tracker.output_tokens == 500
        assert tracker.total_tokens == 1500

    def test_add_usage_accumulates(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1000, 500)
        tracker.add_usage(2000, 1000)
        assert tracker.input_tokens == 3000
        assert tracker.output_tokens == 1500

    def test_add_usage_with_model(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1000, 500, model="claude-sonnet-4-5-20250929")
        assert tracker.input_tokens == 1000
        assert tracker.output_tokens == 500

    def test_add_tool_call(self) -> None:
        tracker = CostTracker()
        tracker.add_tool_call()
        tracker.add_tool_call()
        assert tracker.tool_calls == 2

    def test_total_cost_no_model_uses_opus_pricing(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1_000_000, 100_000)
        # Opus fallback: $15/M input + $75/M output = $15 + $7.5 = $22.5
        assert abs(tracker.total_cost - 22.5) < 0.001

    def test_total_cost_multi_model(self) -> None:
        tracker = CostTracker()
        # Opus: 100k input, 10k output => $1.5 + $0.75 = $2.25
        tracker.add_usage(100_000, 10_000, model="claude-opus-4-6")
        # Sonnet: 500k input, 50k output => $1.5 + $0.75 = $2.25
        tracker.add_usage(500_000, 50_000, model="claude-sonnet-4-5-20250929")
        # Haiku: 200k input, 20k output => $0.16 + $0.08 = $0.24
        tracker.add_usage(200_000, 20_000, model="claude-haiku-4-5-20251001")
        expected = 2.25 + 2.25 + 0.24
        assert abs(tracker.total_cost - expected) < 0.001

    def test_to_dict_without_model(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(100, 50)
        tracker.add_tool_call()
        result = tracker.to_dict()
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["tool_calls"] == 1
        assert isinstance(result["total_cost_usd"], float)
        assert "by_model" not in result

    def test_to_dict_with_model_breakdown(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(100, 50, model="claude-opus-4-6")
        tracker.add_usage(200, 100, model="claude-sonnet-4-5-20250929")
        tracker.add_tool_call()
        result = tracker.to_dict()
        assert result["input_tokens"] == 300
        assert result["output_tokens"] == 150
        assert "by_model" in result
        breakdown = result["by_model"]
        assert isinstance(breakdown, dict)
        assert "claude-opus-4-6" in breakdown
        assert "claude-sonnet-4-5-20250929" in breakdown
        opus_data = breakdown["claude-opus-4-6"]
        assert isinstance(opus_data, dict)
        assert opus_data["input_tokens"] == 100
        assert opus_data["calls"] == 1
