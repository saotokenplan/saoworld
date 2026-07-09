"""成本计算器模块测试。"""

from app.core.cost_calculator import CostCalculator, cost_calculator


class TestCostCalculator:
    def test_calculate_cost_basic(self):
        result = cost_calculator.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=2000,
            daily_used_tokens=10000,
            monthly_used_tokens=50000,
        )

        assert result.token_usage.prompt_tokens == 1000
        assert result.token_usage.completion_tokens == 2000
        assert result.token_usage.total_tokens == 3000
        assert result.cost_usd > 0
        assert not result.should_alert
        assert not result.should_pause

    def test_calculate_cost_alert_threshold(self):
        result = cost_calculator.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=2000,
            daily_used_tokens=800000,
            monthly_used_tokens=24000000,
        )

        assert result.daily_usage_ratio >= 0.8
        assert result.monthly_usage_ratio >= 0.8
        assert result.should_alert

    def test_calculate_cost_pause_threshold(self):
        result = cost_calculator.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=2000,
            daily_used_tokens=950000,
            monthly_used_tokens=28500000,
        )

        assert result.daily_usage_ratio >= 0.95
        assert result.monthly_usage_ratio >= 0.95
        assert result.should_pause

    def test_estimate_cost_for_request(self):
        result = cost_calculator.estimate_cost_for_request(
            estimated_tokens=1000,
            daily_used_tokens=10000,
            monthly_used_tokens=50000,
        )

        assert result.token_usage.prompt_tokens == 300
        assert result.token_usage.completion_tokens == 700
        assert result.token_usage.total_tokens == 1000
        assert result.cost_usd > 0

    def test_cost_with_zero_budget(self):
        calculator = CostCalculator()
        calculator.daily_budget = 0
        calculator.monthly_budget = 0

        result = calculator.calculate_cost(
            prompt_tokens=1000,
            completion_tokens=2000,
            daily_used_tokens=10000,
            monthly_used_tokens=50000,
        )

        assert result.daily_usage_ratio == 0.0
        assert result.monthly_usage_ratio == 0.0
        assert not result.should_alert
        assert not result.should_pause