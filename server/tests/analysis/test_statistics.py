import json

import numpy as np
import pytest

from ehrlich.analysis.application.statistics_service import StatisticsService
from ehrlich.analysis.domain.statistics import StatisticalResult


class TestStatisticalResult:
    def test_frozen(self) -> None:
        r = StatisticalResult(
            test_name="t_test",
            test_statistic=2.5,
            p_value=0.01,
            effect_size=0.8,
            effect_size_type="cohens_d",
            ci_lower=0.3,
            ci_upper=1.3,
            sample_size_a=30,
            sample_size_b=30,
            significant=True,
        )
        with pytest.raises(AttributeError):
            r.p_value = 0.5  # type: ignore[misc]

    def test_invalid_p_value(self) -> None:
        with pytest.raises(ValueError, match="p_value"):
            StatisticalResult(
                test_name="t_test",
                test_statistic=1.0,
                p_value=1.5,
                effect_size=0.0,
                effect_size_type="cohens_d",
                ci_lower=0.0,
                ci_upper=0.0,
                sample_size_a=10,
                sample_size_b=10,
                significant=False,
            )

    def test_invalid_sample_size(self) -> None:
        with pytest.raises(ValueError, match="Sample sizes"):
            StatisticalResult(
                test_name="t_test",
                test_statistic=1.0,
                p_value=0.5,
                effect_size=0.0,
                effect_size_type="cohens_d",
                ci_lower=0.0,
                ci_upper=0.0,
                sample_size_a=0,
                sample_size_b=10,
                significant=False,
            )


class TestStatisticsServiceContinuous:
    def setup_method(self) -> None:
        self.svc = StatisticsService()
        self.rng = np.random.default_rng(42)

    def test_auto_normal_data(self) -> None:
        a = self.rng.normal(10.0, 2.0, 50).tolist()
        b = self.rng.normal(12.0, 2.0, 50).tolist()
        result = self.svc.run_test(a, b)
        assert result.test_name in ("t_test", "welch_t")
        assert 0.0 <= result.p_value <= 1.0
        assert result.effect_size_type == "cohens_d"

    def test_auto_skewed_data(self) -> None:
        a = self.rng.exponential(2.0, 50).tolist()
        b = self.rng.exponential(5.0, 50).tolist()
        result = self.svc.run_test(a, b)
        assert result.test_name == "mann_whitney"

    def test_forced_mann_whitney(self) -> None:
        a = self.rng.normal(10.0, 2.0, 30).tolist()
        b = self.rng.normal(10.0, 2.0, 30).tolist()
        result = self.svc.run_test(a, b, test="mann_whitney")
        assert result.test_name == "mann_whitney"

    def test_significant_difference(self) -> None:
        a = self.rng.normal(10.0, 1.0, 100).tolist()
        b = self.rng.normal(15.0, 1.0, 100).tolist()
        result = self.svc.run_test(a, b)
        assert result.significant is True
        assert result.p_value < 0.05

    def test_no_difference(self) -> None:
        a = self.rng.normal(10.0, 2.0, 100).tolist()
        b = self.rng.normal(10.0, 2.0, 100).tolist()
        result = self.svc.run_test(a, b)
        assert result.p_value > 0.05

    def test_small_sample(self) -> None:
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        result = self.svc.run_test(a, b)
        assert result.sample_size_a == 3
        assert result.sample_size_b == 3

    def test_effect_size_direction(self) -> None:
        a = self.rng.normal(20.0, 2.0, 50).tolist()
        b = self.rng.normal(10.0, 2.0, 50).tolist()
        result = self.svc.run_test(a, b)
        assert result.effect_size > 0  # a > b -> positive d

    def test_too_few_observations(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            self.svc.run_test([1.0], [2.0, 3.0])

    def test_ci_bounds(self) -> None:
        a = self.rng.normal(10.0, 2.0, 50).tolist()
        b = self.rng.normal(12.0, 2.0, 50).tolist()
        result = self.svc.run_test(a, b)
        assert result.ci_lower < result.ci_upper


class TestStatisticsServiceCategorical:
    def setup_method(self) -> None:
        self.svc = StatisticsService()

    def test_2x2_fisher_small_cells(self) -> None:
        table = [[3, 1], [1, 3]]
        result = self.svc.run_categorical_test(table)
        assert result.test_name == "fisher_exact"
        assert result.effect_size_type == "odds_ratio"

    def test_2x2_chi_squared_large_cells(self) -> None:
        table = [[50, 30], [20, 60]]
        result = self.svc.run_categorical_test(table)
        assert result.test_name == "chi_squared"
        assert result.effect_size_type == "odds_ratio"

    def test_larger_table(self) -> None:
        table = [[30, 20, 10], [10, 20, 30]]
        result = self.svc.run_categorical_test(table)
        assert result.test_name == "chi_squared"
        assert result.effect_size_type == "cramers_v"

    def test_significant_association(self) -> None:
        table = [[50, 5], [5, 50]]
        result = self.svc.run_categorical_test(table)
        assert result.significant is True

    def test_no_association(self) -> None:
        table = [[25, 25], [25, 25]]
        result = self.svc.run_categorical_test(table)
        assert result.significant is False

    def test_invalid_table(self) -> None:
        with pytest.raises(ValueError, match="at least 2x2"):
            self.svc.run_categorical_test([[1, 2]])

    def test_forced_chi_squared(self) -> None:
        table = [[3, 1], [1, 3]]
        result = self.svc.run_categorical_test(table, test="chi_squared")
        assert result.test_name == "chi_squared"


class TestToolFunctions:
    @pytest.mark.asyncio
    async def test_run_statistical_test_json(self) -> None:
        from ehrlich.analysis.tools import run_statistical_test

        result = json.loads(
            await run_statistical_test(
                [1.0, 2.0, 3.0, 4.0, 5.0],
                [6.0, 7.0, 8.0, 9.0, 10.0],
            )
        )
        assert "test_name" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "significant" in result
        assert "interpretation" in result

    @pytest.mark.asyncio
    async def test_run_categorical_test_json(self) -> None:
        from ehrlich.analysis.tools import run_categorical_test

        result = json.loads(await run_categorical_test([[10, 5], [3, 12]]))
        assert "test_name" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert "significant" in result

    @pytest.mark.asyncio
    async def test_run_statistical_test_error(self) -> None:
        from ehrlich.analysis.tools import run_statistical_test

        result = json.loads(await run_statistical_test([1.0], [2.0, 3.0]))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_categorical_test_error(self) -> None:
        from ehrlich.analysis.tools import run_categorical_test

        result = json.loads(await run_categorical_test([[1, 2]]))
        assert "error" in result
