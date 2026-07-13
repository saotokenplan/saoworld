"""threshold 模块单元测试。"""


from perf_test.stats import LatencyStats
from perf_test.threshold import (
    DEFAULT_THRESHOLDS,
    Threshold,
    check_thresholds,
    get_default_thresholds,
)


class TestCheckThresholds:
    """check_thresholds 行为测试。"""

    def test_all_passed(self) -> None:
        stats = LatencyStats(
            count=100,
            error_count=0,
            p50_ms=20.0,
            p95_ms=80.0,
            p99_ms=150.0,
            error_rate=0.0,
        )
        thresholds = [
            Threshold(name="t1", metric="p95_ms", max_value=100.0),
            Threshold(name="t2", metric="p99_ms", max_value=200.0),
        ]
        summary = check_thresholds(stats, thresholds)
        assert summary.passed is True
        assert len(summary.blocker_failed) == 0
        assert all(r.passed for r in summary.results)

    def test_blocker_failed(self) -> None:
        stats = LatencyStats(p95_ms=350.0, p99_ms=600.0, error_rate=0.05)
        thresholds = [
            Threshold(name="p95", metric="p95_ms", max_value=300.0, severity="blocker"),
            Threshold(name="p99", metric="p99_ms", max_value=500.0, severity="warn"),
            Threshold(name="err", metric="error_rate", max_value=0.01, severity="blocker"),
        ]
        summary = check_thresholds(stats, thresholds)
        assert summary.passed is False
        assert len(summary.blocker_failed) == 2
        warn_failed = [r for r in summary.results if r.severity == "warn" and not r.passed]
        assert len(warn_failed) == 1  # p99 warn failed
        # warn 级别不阻塞总体通过判断
        # 但本例 p95 和 err 都是 blocker 失败 → 整体失败

    def test_warn_only_does_not_fail(self) -> None:
        # 仅 warn 失败不阻塞通过
        stats = LatencyStats(p95_ms=80.0, p99_ms=300.0, error_rate=0.0)
        thresholds = [
            Threshold(name="p95", metric="p95_ms", max_value=100.0, severity="blocker"),
            Threshold(name="p99", metric="p99_ms", max_value=200.0, severity="warn"),
        ]
        summary = check_thresholds(stats, thresholds)
        # warn 失败不计入 blocker_failed
        assert summary.passed is True
        assert len(summary.blocker_failed) == 0

    def test_unknown_metric_fails(self) -> None:
        stats = LatencyStats()
        thresholds = [Threshold(name="bad", metric="unknown_metric", max_value=100.0)]
        summary = check_thresholds(stats, thresholds)
        assert summary.passed is False
        assert summary.results[0].passed is False

    def test_to_dict(self) -> None:
        stats = LatencyStats(p95_ms=80.0)
        thresholds = [Threshold(name="p95", metric="p95_ms", max_value=100.0)]
        summary = check_thresholds(stats, thresholds)
        d = summary.to_dict()
        assert d["passed"] is True
        assert d["blocker_failed"] == []
        results = d["results"]
        assert isinstance(results, list)
        assert len(results) == 1
        first = results[0]
        assert isinstance(first, dict)
        assert first["name"] == "p95"


class TestDefaultThresholds:
    """默认阈值配置测试。"""

    def test_vote_submit_default(self) -> None:
        ths = get_default_thresholds("vote_submit")
        assert len(ths) >= 2
        p95 = next(t for t in ths if t.metric == "p95_ms")
        assert p95.max_value == 300.0
        assert p95.severity == "blocker"

    def test_vote_query_default(self) -> None:
        ths = get_default_thresholds("vote_query")
        p95 = next(t for t in ths if t.metric == "p95_ms")
        assert p95.max_value == 100.0
        assert p95.severity == "blocker"

    def test_content_query_default(self) -> None:
        ths = get_default_thresholds("content_query")
        p95 = next(t for t in ths if t.metric == "p95_ms")
        assert p95.max_value == 100.0
        assert p95.severity == "blocker"

    def test_unknown_scenario_returns_empty(self) -> None:
        ths = get_default_thresholds("unknown_scenario")
        assert ths == []

    def test_all_scenarios_have_thresholds(self) -> None:
        assert "vote_submit" in DEFAULT_THRESHOLDS
        assert "vote_query" in DEFAULT_THRESHOLDS
        assert "content_query" in DEFAULT_THRESHOLDS
