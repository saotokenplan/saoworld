"""WP3 审核效率监控指标埋点测试（M1/M2/M3/M4）。

覆盖 M4-审核效率看板指标定义.md 第三节缺口清单的实施期改造：
- M1: review_duration_seconds Histogram 在审核终结时记录耗时
- M2: reviews_total 增加 review_type 标签，auto 路径对所有终局判定计数
- M4: review_rule_decisions_total 规则归因 Counter 在引擎评估处埋点
- M3: 标签口径与 metrics.yaml 一致（在 metrics.yaml 同步提交中落地，本测试校验代码侧标签可被正确取值）

使用 prometheus_client.REGISTRY.get_sample_value 按标签读取当前值并以 delta 断言，
避免受同会话其它用例累积影响。
"""

import pytest
from prometheus_client import REGISTRY

from app.core.auto_review_engine import auto_review_engine
from app.core.metrics import record_review_duration, record_review_result


def _sample_delta(name: str, labels: dict, fn) -> float:
    before = REGISTRY.get_sample_value(name, labels) or 0.0
    fn()
    after = REGISTRY.get_sample_value(name, labels) or 0.0
    return after - before


class TestM2ReviewsTotalReviewType:
    """M2: reviews_total 区分 auto/manual，auto 路径全终局计数。"""

    def test_auto_and_manual_approved_distinguished(self):
        delta_auto = _sample_delta(
            "reviews_total",
            {"result": "approved", "review_type": "auto"},
            lambda: record_review_result("approved", "auto"),
        )
        delta_manual = _sample_delta(
            "reviews_total",
            {"result": "approved", "review_type": "manual"},
            lambda: record_review_result("approved", "manual"),
        )
        assert delta_auto == pytest.approx(1)
        assert delta_manual == pytest.approx(1)

    def test_rejected_counted_by_type(self):
        delta = _sample_delta(
            "reviews_total",
            {"result": "rejected", "review_type": "manual"},
            lambda: record_review_result("rejected", "manual"),
        )
        assert delta == pytest.approx(1)

    def test_manual_review_terminal_counted_for_auto(self):
        # M2 核心修复：auto 路径对 manual_review 终局也计数（此前仅 is_automatic 时计数）
        delta = _sample_delta(
            "reviews_total",
            {"result": "manual_review", "review_type": "auto"},
            lambda: record_review_result("manual_review", "auto"),
        )
        assert delta == pytest.approx(1)


class TestM1ReviewDuration:
    """M1: review_duration_seconds Histogram 记录耗时（K2 在线数据源）。"""

    def test_auto_observation_increments_sum(self):
        delta = _sample_delta(
            "review_duration_seconds_sum",
            {"review_type": "auto", "object_type": "region"},
            lambda: record_review_duration("auto", "region", 12.5),
        )
        assert delta == pytest.approx(12.5)

    def test_manual_observation_increments_sum(self):
        delta = _sample_delta(
            "review_duration_seconds_sum",
            {"review_type": "manual", "object_type": "item"},
            lambda: record_review_duration("manual", "item", 3.0),
        )
        assert delta == pytest.approx(3.0)


class TestM4RuleDecisions:
    """M4: review_rule_decisions_total 规则归因埋点。"""

    def test_quality_score_rule_approved_recorded(self):
        payload = {
            "item_key": "i1",
            "item_type": "weapon",
            "name": "Blade",
            "rarity": "common",
            "level_requirement": 5,
        }
        delta = _sample_delta(
            "review_rule_decisions_total",
            {"rule": "QualityScoreRule", "result": "approved"},
            lambda: auto_review_engine.evaluate("item", payload, quality_score=0.95),
        )
        assert delta == pytest.approx(1)

    def test_content_safety_rule_rejected_recorded(self):
        payload = {"description": "这是一段包含暴力血腥内容的描述用于测试"}
        delta = _sample_delta(
            "review_rule_decisions_total",
            {"rule": "ContentSafetyRule", "result": "rejected"},
            lambda: auto_review_engine.evaluate("region", payload, quality_score=0.9),
        )
        assert delta == pytest.approx(1)

    def test_not_applied_recorded_for_inapplicable_rule(self):
        # object_type 不在 REQUIRED_FIELDS_BY_TYPE 中 -> FieldCompletenessRule 返回 None -> not_applied
        payload = {"foo": "bar"}
        delta = _sample_delta(
            "review_rule_decisions_total",
            {"rule": "FieldCompletenessRule", "result": "not_applied"},
            lambda: auto_review_engine.evaluate("unknown_type", payload, quality_score=0.9),
        )
        assert delta == pytest.approx(1)
