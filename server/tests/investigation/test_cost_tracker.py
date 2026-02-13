from ehrlich.investigation.application.cost_tracker import CostTracker


class TestCostTracker:
    def test_initial_state(self) -> None:
        tracker = CostTracker()
        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0
        assert tracker.cache_read_tokens == 0
        assert tracker.cache_write_tokens == 0
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

    def test_total_cost_no_model_uses_default_pricing(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1_000_000, 100_000)
        # Default: $5/M input + $25/M output = $5 + $2.5 = $7.5
        assert abs(tracker.total_cost - 7.5) < 0.001

    def test_total_cost_multi_model(self) -> None:
        tracker = CostTracker()
        # Opus: 100k in * $5/M + 10k out * $25/M = $0.50 + $0.25 = $0.75
        tracker.add_usage(100_000, 10_000, model="claude-opus-4-6")
        # Sonnet: 500k in * $3/M + 50k out * $15/M = $1.50 + $0.75 = $2.25
        tracker.add_usage(500_000, 50_000, model="claude-sonnet-4-5-20250929")
        # Haiku: 200k in * $1/M + 20k out * $5/M = $0.20 + $0.10 = $0.30
        tracker.add_usage(200_000, 20_000, model="claude-haiku-4-5-20251001")
        expected = 0.75 + 2.25 + 0.30
        assert abs(tracker.total_cost - expected) < 0.001

    def test_to_dict_without_model(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(100, 50)
        tracker.add_tool_call()
        result = tracker.to_dict()
        assert result["input_tokens"] == 100
        assert result["output_tokens"] == 50
        assert result["cache_read_tokens"] == 0
        assert result["cache_write_tokens"] == 0
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

    def test_cache_aware_cost_calculation(self) -> None:
        tracker = CostTracker()
        # Opus: 100k input, 10k output, 50k cache_write, 200k cache_read
        # input: 100k * $5/M = $0.50
        # cache_write: 50k * $5/M * 1.25 = $0.3125
        # cache_read: 200k * $5/M * 0.1 = $0.10
        # output: 10k * $25/M = $0.25
        # total = $1.1625
        tracker.add_usage(
            100_000,
            10_000,
            model="claude-opus-4-6",
            cache_write_tokens=50_000,
            cache_read_tokens=200_000,
        )
        assert abs(tracker.total_cost - 1.1625) < 0.0001

    def test_cache_tokens_accumulate(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(
            100, 50, model="claude-opus-4-6", cache_read_tokens=500, cache_write_tokens=200
        )
        tracker.add_usage(
            200, 100, model="claude-opus-4-6", cache_read_tokens=300, cache_write_tokens=100
        )
        assert tracker.cache_read_tokens == 800
        assert tracker.cache_write_tokens == 300
        assert tracker.input_tokens == 300
        assert tracker.output_tokens == 150

    def test_cache_tokens_in_to_dict(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(1000, 500, cache_read_tokens=2000, cache_write_tokens=1000)
        result = tracker.to_dict()
        assert result["cache_read_tokens"] == 2000
        assert result["cache_write_tokens"] == 1000

    def test_cache_tokens_per_model_breakdown(self) -> None:
        tracker = CostTracker()
        tracker.add_usage(
            100,
            50,
            model="claude-opus-4-6",
            cache_read_tokens=500,
            cache_write_tokens=200,
        )
        tracker.add_usage(
            200,
            100,
            model="claude-sonnet-4-5-20250929",
            cache_read_tokens=300,
            cache_write_tokens=150,
        )
        result = tracker.to_dict()
        breakdown = result["by_model"]
        assert isinstance(breakdown, dict)
        opus = breakdown["claude-opus-4-6"]
        assert isinstance(opus, dict)
        assert opus["cache_read_tokens"] == 500
        assert opus["cache_write_tokens"] == 200
        sonnet = breakdown["claude-sonnet-4-5-20250929"]
        assert isinstance(sonnet, dict)
        assert sonnet["cache_read_tokens"] == 300
        assert sonnet["cache_write_tokens"] == 150
