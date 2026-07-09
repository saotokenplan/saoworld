"""成本计算器模块，负责 Token 用量统计和成本估算。"""

import structlog
from dataclasses import dataclass

from app.core.config import settings

logger = structlog.get_logger()


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class CostResult:
    token_usage: TokenUsage
    cost_usd: float
    daily_remaining_tokens: int
    monthly_remaining_tokens: int
    daily_usage_ratio: float
    monthly_usage_ratio: float
    should_alert: bool
    should_pause: bool


class CostCalculator:
    def __init__(self):
        self.daily_budget = settings.cost_daily_budget_tokens
        self.monthly_budget = settings.cost_monthly_budget_tokens
        self.alert_threshold = settings.cost_alert_threshold_ratio
        self.pause_threshold = settings.cost_pause_threshold_ratio
        self.price_per_1k_prompt = settings.cost_model_price_per_1k_prompt_tokens
        self.price_per_1k_completion = settings.cost_model_price_per_1k_completion_tokens

    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        daily_used_tokens: int,
        monthly_used_tokens: int,
    ) -> CostResult:
        total_tokens = prompt_tokens + completion_tokens

        prompt_cost = (prompt_tokens / 1000) * self.price_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self.price_per_1k_completion
        total_cost = prompt_cost + completion_cost

        daily_remaining = max(0, self.daily_budget - daily_used_tokens)
        monthly_remaining = max(0, self.monthly_budget - monthly_used_tokens)

        daily_ratio = min(1.0, daily_used_tokens / self.daily_budget) if self.daily_budget > 0 else 0.0
        monthly_ratio = min(1.0, monthly_used_tokens / self.monthly_budget) if self.monthly_budget > 0 else 0.0

        should_alert = daily_ratio >= self.alert_threshold or monthly_ratio >= self.alert_threshold
        should_pause = daily_ratio >= self.pause_threshold or monthly_ratio >= self.pause_threshold

        if should_alert:
            logger.warning(
                "cost_alert_triggered",
                daily_ratio=daily_ratio,
                monthly_ratio=monthly_ratio,
                daily_used=daily_used_tokens,
                monthly_used=monthly_used_tokens,
            )

        if should_pause:
            logger.error(
                "cost_pause_triggered",
                daily_ratio=daily_ratio,
                monthly_ratio=monthly_ratio,
                daily_used=daily_used_tokens,
                monthly_used=monthly_used_tokens,
            )

        return CostResult(
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
            cost_usd=total_cost,
            daily_remaining_tokens=daily_remaining,
            monthly_remaining_tokens=monthly_remaining,
            daily_usage_ratio=daily_ratio,
            monthly_usage_ratio=monthly_ratio,
            should_alert=should_alert,
            should_pause=should_pause,
        )

    def estimate_cost_for_request(
        self,
        estimated_tokens: int,
        daily_used_tokens: int,
        monthly_used_tokens: int,
    ) -> CostResult:
        return self.calculate_cost(
            prompt_tokens=int(estimated_tokens * 0.3),
            completion_tokens=int(estimated_tokens * 0.7),
            daily_used_tokens=daily_used_tokens,
            monthly_used_tokens=monthly_used_tokens,
        )


cost_calculator = CostCalculator()