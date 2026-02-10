from ehrlich.investigation.application.cost_tracker import CostTracker


class TestCostTracker:
    def test_initial_state(self) -> None:
        tracker = CostTracker()
        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0
        assert tracker.tool_calls == 0
        assert tracker.total_cost == 0.0
        assert tracker.total_tokens == 0

    def test_add_usage(self) -> None:
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

    def test_add_tool_call(self) -> None:
        tracker = CostTracker()
        tracker.add_tool_call()
        tracker.add_tool_call()
        assert tracker.tool_calls == 2

    def test_total_cost_calculation(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1_000_000, 100_000)
        # $3/M input + $15/M output = $3 + $1.5 = $4.5
        assert abs(tracker.total_cost - 4.5) < 0.001

    def test_to_dict(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(100, 50)
        tracker.add_tool_call()
        result = tracker.to_dict()
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["tool_calls"] == 1
        assert isinstance(result["total_cost_usd"], float)
