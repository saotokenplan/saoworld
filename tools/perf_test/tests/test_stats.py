"""stats 模块单元测试。"""

import pytest

from perf_test.stats import _percentile, compute_stats


class TestPercentile:
    """百分位数计算测试。"""

    def test_empty_returns_zero(self) -> None:
        assert _percentile([], 50) == 0.0

    def test_p_zero_returns_min(self) -> None:
        assert _percentile([1.0, 2.0, 3.0], 0) == 1.0

    def test_p_hundred_returns_max(self) -> None:
        assert _percentile([1.0, 2.0, 3.0], 100) == 3.0

    def test_p50_single_value(self) -> None:
        assert _percentile([42.0], 50) == 42.0

    def test_p50_even_count(self) -> None:
        # [10, 20, 30, 40] → p50 介于 index 1.5，即 (20+30)/2 = 25
        assert _percentile([10.0, 20.0, 30.0, 40.0], 50) == 25.0

    def test_p95_known_distribution(self) -> None:
        # 100 个值 [1..100]，p95 的 rank = 0.95 * 99 = 94.05
        # → sorted[94] * 0.95 + sorted[95] * 0.05 = 95 * 0.95 + 96 * 0.05 = 95.05
        values = [float(i) for i in range(1, 101)]
        result = _percentile(values, 95)
        assert result == pytest.approx(95.05, rel=1e-3)

    def test_p99_known_distribution(self) -> None:
        # rank = 0.99 * 99 = 98.01
        # → sorted[98] * 0.99 + sorted[99] * 0.01 = 99 * 0.99 + 100 * 0.01 = 99.01
        values = [float(i) for i in range(1, 101)]
        result = _percentile(values, 99)
        assert result == pytest.approx(99.01, rel=1e-2)

    def test_p95_small_sample(self) -> None:
        # 20 个值 [1..20]，rank = 0.95 * 19 = 18.05
        # → sorted[18] * 0.95 + sorted[19] * 0.05 = 19 * 0.95 + 20 * 0.05 = 19.05
        values = [float(i) for i in range(1, 21)]
        result = _percentile(values, 95)
        assert result == pytest.approx(19.05, rel=1e-3)


class TestComputeStats:
    """compute_stats 集成测试。"""

    def test_empty_input(self) -> None:
        stats = compute_stats([], error_count=0, duration_seconds=0.0)
        assert stats.count == 0
        assert stats.error_count == 0
        assert stats.qps == 0.0
        assert stats.error_rate == 0.0

    def test_all_success(self) -> None:
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = compute_stats(latencies, error_count=0, duration_seconds=1.0)
        assert stats.count == 5
        assert stats.error_count == 0
        assert stats.min_ms == 10.0
        assert stats.max_ms == 50.0
        assert stats.avg_ms == 30.0
        assert stats.p50_ms == 30.0
        assert stats.qps == 5.0
        assert stats.error_rate == 0.0

    def test_all_errors(self) -> None:
        stats = compute_stats([], error_count=10, duration_seconds=2.0)
        assert stats.count == 10
        assert stats.error_count == 10
        assert stats.error_rate == 1.0
        assert stats.qps == 5.0
        assert stats.p95_ms == 0.0  # 全部失败时无延迟数据

    def test_mixed_success_and_errors(self) -> None:
        latencies = [100.0, 200.0, 300.0]
        stats = compute_stats(latencies, error_count=2, duration_seconds=1.0)
        assert stats.count == 5
        assert stats.error_count == 2
        assert stats.error_rate == pytest.approx(0.4, rel=1e-3)
        assert stats.qps == 5.0
        assert stats.avg_ms == 200.0

    def test_p95_under_threshold(self) -> None:
        # 100 个值，p95 应 < 100
        latencies = [float(i) for i in range(1, 101)]
        stats = compute_stats(latencies, error_count=0, duration_seconds=10.0)
        assert stats.p95_ms < 100.0

    def test_to_dict(self) -> None:
        stats = compute_stats([10.0, 20.0], error_count=0, duration_seconds=1.0)
        d = stats.to_dict()
        assert d["count"] == 2
        assert d["min_ms"] == 10.0
        assert d["max_ms"] == 20.0
        assert "p95_ms" in d
        assert "qps" in d

    def test_duration_zero_no_qps(self) -> None:
        stats = compute_stats([10.0], error_count=0, duration_seconds=0.0)
        assert stats.qps == 0.0

    def test_large_qps(self) -> None:
        stats = compute_stats([1.0] * 1000, error_count=0, duration_seconds=1.0)
        assert stats.qps == 1000.0
        assert stats.count == 1000
        assert stats.error_rate == 0.0
