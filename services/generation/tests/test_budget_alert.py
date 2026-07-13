"""预算告警模块测试。"""

from app.core.budget_alert import budget_alert_manager


class TestBudgetAlertManager:
    def test_check_daily_budget_no_alert(self):
        alerts = budget_alert_manager.check_daily_budget(100000)
        assert len(alerts) == 0

    def test_check_daily_budget_warning(self):
        alerts = budget_alert_manager.check_daily_budget(800000)
        assert len(alerts) == 1
        assert alerts[0].level == "warning"
        assert "每日 Token 预算" in alerts[0].message

    def test_check_daily_budget_error(self):
        alerts = budget_alert_manager.check_daily_budget(950000)
        assert len(alerts) == 1
        assert alerts[0].level == "error"
        assert "应暂停生成" in alerts[0].message

    def test_check_monthly_budget_no_alert(self):
        alerts = budget_alert_manager.check_monthly_budget(5000000)
        assert len(alerts) == 0

    def test_check_monthly_budget_warning(self):
        alerts = budget_alert_manager.check_monthly_budget(24000000)
        assert len(alerts) == 1
        assert alerts[0].level == "warning"
        assert "每月 Token 预算" in alerts[0].message

    def test_check_monthly_budget_error(self):
        alerts = budget_alert_manager.check_monthly_budget(28500000)
        assert len(alerts) == 1
        assert alerts[0].level == "error"
        assert "应暂停生成" in alerts[0].message

    def test_check_all_budgets_both_warnings(self):
        alerts = budget_alert_manager.check_all_budgets(800000, 24000000)
        assert len(alerts) == 2
        levels = [a.level for a in alerts]
        assert "warning" in levels

    def test_check_all_budgets_daily_error_monthly_warning(self):
        alerts = budget_alert_manager.check_all_budgets(950000, 24000000)
        assert len(alerts) == 2
        levels = [a.level for a in alerts]
        assert "error" in levels
        assert "warning" in levels

    def test_should_pause_generation_false(self):
        result = budget_alert_manager.should_pause_generation(100000, 5000000)
        assert result is False

    def test_should_pause_generation_true_daily(self):
        result = budget_alert_manager.should_pause_generation(950000, 5000000)
        assert result is True

    def test_should_pause_generation_true_monthly(self):
        result = budget_alert_manager.should_pause_generation(100000, 28500000)
        assert result is True
