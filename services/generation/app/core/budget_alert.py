"""预算告警模块，负责监控 Token 使用情况并触发告警。"""

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from app.core.config import settings

logger = structlog.get_logger()


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class BudgetAlert:
    level: AlertLevel
    message: str
    period: str
    used_tokens: int
    budget_tokens: int
    usage_ratio: float
    occurred_at: datetime


class BudgetAlertManager:
    def __init__(self):
        self.daily_budget = settings.cost_daily_budget_tokens
        self.monthly_budget = settings.cost_monthly_budget_tokens
        self.alert_threshold = settings.cost_alert_threshold_ratio
        self.pause_threshold = settings.cost_pause_threshold_ratio

    def check_daily_budget(self, daily_used_tokens: int) -> list[BudgetAlert]:
        alerts: list[BudgetAlert] = []
        ratio = min(1.0, daily_used_tokens / self.daily_budget) if self.daily_budget > 0 else 0.0

        if ratio >= self.pause_threshold:
            alerts.append(
                BudgetAlert(
                    level=AlertLevel.ERROR,
                    message=f"每日 Token 预算已达 {ratio:.1%}，应暂停生成",
                    period="daily",
                    used_tokens=daily_used_tokens,
                    budget_tokens=self.daily_budget,
                    usage_ratio=ratio,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            logger.error(
                "budget_pause_triggered",
                period="daily",
                used=daily_used_tokens,
                budget=self.daily_budget,
                ratio=ratio,
            )
        elif ratio >= self.alert_threshold:
            alerts.append(
                BudgetAlert(
                    level=AlertLevel.WARNING,
                    message=f"每日 Token 预算已达 {ratio:.1%}，即将接近上限",
                    period="daily",
                    used_tokens=daily_used_tokens,
                    budget_tokens=self.daily_budget,
                    usage_ratio=ratio,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            logger.warning(
                "budget_alert_triggered",
                period="daily",
                used=daily_used_tokens,
                budget=self.daily_budget,
                ratio=ratio,
            )

        return alerts

    def check_monthly_budget(self, monthly_used_tokens: int) -> list[BudgetAlert]:
        alerts: list[BudgetAlert] = []
        ratio = min(1.0, monthly_used_tokens / self.monthly_budget) if self.monthly_budget > 0 else 0.0

        if ratio >= self.pause_threshold:
            alerts.append(
                BudgetAlert(
                    level=AlertLevel.ERROR,
                    message=f"每月 Token 预算已达 {ratio:.1%}，应暂停生成",
                    period="monthly",
                    used_tokens=monthly_used_tokens,
                    budget_tokens=self.monthly_budget,
                    usage_ratio=ratio,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            logger.error(
                "budget_pause_triggered",
                period="monthly",
                used=monthly_used_tokens,
                budget=self.monthly_budget,
                ratio=ratio,
            )
        elif ratio >= self.alert_threshold:
            alerts.append(
                BudgetAlert(
                    level=AlertLevel.WARNING,
                    message=f"每月 Token 预算已达 {ratio:.1%}，即将接近上限",
                    period="monthly",
                    used_tokens=monthly_used_tokens,
                    budget_tokens=self.monthly_budget,
                    usage_ratio=ratio,
                    occurred_at=datetime.now(timezone.utc),
                )
            )
            logger.warning(
                "budget_alert_triggered",
                period="monthly",
                used=monthly_used_tokens,
                budget=self.monthly_budget,
                ratio=ratio,
            )

        return alerts

    def check_all_budgets(self, daily_used: int, monthly_used: int) -> list[BudgetAlert]:
        alerts = []
        alerts.extend(self.check_daily_budget(daily_used))
        alerts.extend(self.check_monthly_budget(monthly_used))
        return alerts

    def should_pause_generation(self, daily_used: int, monthly_used: int) -> bool:
        daily_ratio: float = min(1.0, daily_used / self.daily_budget) if self.daily_budget > 0 else 0.0
        monthly_ratio: float = min(1.0, monthly_used / self.monthly_budget) if self.monthly_budget > 0 else 0.0
        should_pause: bool = daily_ratio >= self.pause_threshold or monthly_ratio >= self.pause_threshold
        return should_pause


budget_alert_manager = BudgetAlertManager()