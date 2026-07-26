"""WP3 ops 看板三字段：审核效率派生指标测试。

覆盖：
- 纯函数 compute_review_efficiency / histogram_quantile 的正确性（含 None 边界）
- GET /api/v1/review/stats 端点从 REGISTRY 派生三项字段并可被集成测试断言
"""

import pytest

from app.core.metrics import record_review_duration, record_review_result
from app.core.review_efficiency import (
    compute_review_efficiency,
    histogram_quantile,
)


# ---------------------------------------------------------------------------
# 纯函数：histogram_quantile
# ---------------------------------------------------------------------------


class TestHistogramQuantile:
    def test_median_within_bucket(self):
        # 桶 [10,20,30]，累计 [5,10,20]，总数 20，P50 rank=10 -> 落在 [10,20] 桶，frac=1.0 -> 20
        assert histogram_quantile(0.5, [10, 20, 30], [5, 10, 20]) == pytest.approx(20.0)

    def test_p95_interpolated(self):
        # 桶 [10,20,30]，累计 [5,10,20]，P95 rank=19 -> [20,30] 桶，frac=0.9 -> 29
        assert histogram_quantile(0.95, [10, 20, 30], [5, 10, 20]) == pytest.approx(29.0)

    def test_empty_buckets_returns_none(self):
        assert histogram_quantile(0.95, [], []) is None

    def test_zero_total_returns_none(self):
        assert histogram_quantile(0.95, [10, 20], [0, 0]) is None

    def test_skips_zero_count_bucket(self):
        # 中间桶无样本，应向后找到首个非空桶
        # 桶 [10,20,30,40]，累计 [0,0,15,20]，P95 rank=19 -> [30,40] 桶，frac=(19-15)/5=0.8 -> 38
        assert histogram_quantile(0.95, [10, 20, 30, 40], [0, 0, 15, 20]) == pytest.approx(38.0)


# ---------------------------------------------------------------------------
# 纯函数：compute_review_efficiency
# ---------------------------------------------------------------------------


class TestComputeReviewEfficiency:
    def test_mixed_counts(self):
        review_counts = {
            ("approved", "auto"): 8,
            ("rejected", "auto"): 2,
            ("approved", "manual"): 1,
            ("rejected", "manual"): 1,
        }
        duration = {"buckets": [10, 20, 30], "cumulative": [5, 10, 20], "count": 20, "sum": 240.0}
        result = compute_review_efficiency(review_counts, duration)
        assert result["auto_pass_rate"] == pytest.approx(8 / 10)
        assert result["manual_intervention_rate"] == pytest.approx(2 / 12)
        assert result["review_p95_minutes"] == pytest.approx(29.0 / 60.0)

    def test_no_reviews_returns_none(self):
        result = compute_review_efficiency({}, {"buckets": [], "cumulative": [], "count": 0, "sum": 0.0})
        assert result["auto_pass_rate"] is None
        assert result["manual_intervention_rate"] is None
        assert result["review_p95_minutes"] is None

    def test_auto_total_zero_keeps_manual_rate(self):
        # 仅有 manual 审核：auto_pass_rate 应为 None，manual_intervention_rate 仍可算
        review_counts = {("approved", "manual"): 3, ("rejected", "manual"): 1}
        result = compute_review_efficiency(review_counts, {"buckets": [], "cumulative": [], "count": 0, "sum": 0.0})
        assert result["auto_pass_rate"] is None
        assert result["manual_intervention_rate"] == pytest.approx(4 / 4)
        assert result["review_p95_minutes"] is None


# ---------------------------------------------------------------------------
# 端点集成：GET /api/v1/review/stats（seed REGISTRY）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_stats_endpoint_returns_three_fields(client):
    # 种子 reviews_total 与 review_duration_seconds（以 delta 增量，避免受会话累计影响断言结构）
    record_review_result("approved", "auto")
    record_review_result("approved", "auto")
    record_review_result("rejected", "auto")
    record_review_result("approved", "manual")
    record_review_duration("auto", "region", 12.0)
    record_review_duration("auto", "region", 5.0)
    record_review_duration("manual", "item", 3.0)

    resp = await client.get("/api/v1/review/stats")
    assert resp.status_code == 200
    data = resp.json()["data"]

    # 三项字段均存在且为 float（种子已产生样本）
    assert isinstance(data["auto_pass_rate"], float)
    assert isinstance(data["manual_intervention_rate"], float)
    assert isinstance(data["review_p95_minutes"], float)
    # raw 透出便于排障
    assert "raw" in data
    assert data["raw"]["duration_count"] >= 3


@pytest.mark.asyncio
async def test_review_stats_endpoint_structure_only(client):
    # 即便无样本，端点也应 200 且三项为 None（不抛错）
    resp = await client.get("/api/v1/review/stats")
    assert resp.status_code == 200
    data = resp.json()["data"]
    for key in ("auto_pass_rate", "manual_intervention_rate", "review_p95_minutes"):
        assert key in data
