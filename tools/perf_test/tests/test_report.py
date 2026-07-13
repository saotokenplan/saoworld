"""report 模块单元测试。"""

import json


from perf_test.report import ReportFormat, ScenarioReport, generate_report
from perf_test.stats import LatencyStats
from perf_test.threshold import Threshold, check_thresholds


def _make_stats(**overrides: float) -> LatencyStats:
    defaults: dict[str, int | float] = {
        "count": 100,
        "error_count": 0,
        "min_ms": 10.0,
        "max_ms": 200.0,
        "avg_ms": 50.0,
        "p50_ms": 45.0,
        "p95_ms": 180.0,
        "p99_ms": 195.0,
        "qps": 50.0,
        "duration_seconds": 2.0,
        "error_rate": 0.0,
    }
    defaults.update(overrides)
    return LatencyStats(**defaults)  # type: ignore[arg-type]


def _make_report(
    name: str = "test_scenario",
    description: str = "Test description",
    stats: LatencyStats | None = None,
    with_thresholds: bool = True,
) -> ScenarioReport:
    s = stats or _make_stats()
    summary = None
    if with_thresholds:
        thresholds = [
            Threshold(name="p95", metric="p95_ms", max_value=300.0, severity="blocker"),
            Threshold(name="err", metric="error_rate", max_value=0.01, severity="blocker"),
        ]
        summary = check_thresholds(s, thresholds)
    return ScenarioReport(
        name=name,
        description=description,
        stats=s,
        threshold_summary=summary,
        config={"path": "/test"},
    )


class TestReportFormat:
    """报告生成测试。"""

    def test_markdown_contains_scenario_name(self) -> None:
        report = _make_report(name="vote_submit")
        md = generate_report([report], fmt=ReportFormat.MARKDOWN)
        assert "vote_submit" in md
        assert "Test description" in md
        assert "性能压测报告" in md

    def test_markdown_contains_p95_value(self) -> None:
        report = _make_report()
        md = generate_report([report], fmt=ReportFormat.MARKDOWN)
        # p95 应该是 180.00 ms
        assert "180.00" in md
        assert "p95" in md

    def test_markdown_shows_passed_status(self) -> None:
        report = _make_report()  # 阈值默认通过
        md = generate_report([report], fmt=ReportFormat.MARKDOWN)
        assert "PASS" in md

    def test_markdown_shows_failed_status(self) -> None:
        stats = _make_stats(p95_ms=400.0)  # 超过 300ms
        report = _make_report(stats=stats)
        md = generate_report([report], fmt=ReportFormat.MARKDOWN)
        assert "FAIL" in md
        assert "blocker 失败" in md

    def test_markdown_without_thresholds(self) -> None:
        report = _make_report(name="vote_query", with_thresholds=False)
        md = generate_report([report], fmt=ReportFormat.MARKDOWN)
        assert "阈值校验" not in md
        assert "vote_query" in md

    def test_json_is_valid_json(self) -> None:
        report = _make_report()
        out = generate_report([report], fmt=ReportFormat.JSON)
        parsed = json.loads(out)
        assert "generated_at" in parsed
        assert parsed["scenario_count"] == 1
        assert parsed["scenarios"][0]["name"] == "test_scenario"
        assert parsed["scenarios"][0]["stats"]["p95_ms"] == 180.0

    def test_json_contains_threshold_summary(self) -> None:
        report = _make_report()
        out = generate_report([report], fmt=ReportFormat.JSON)
        parsed = json.loads(out)
        ts = parsed["scenarios"][0]["threshold_summary"]
        assert ts["passed"] is True
        assert len(ts["results"]) == 2

    def test_multiple_reports(self) -> None:
        report1 = _make_report(name="a")
        report2 = _make_report(name="b")
        md = generate_report([report1, report2], fmt=ReportFormat.MARKDOWN)
        assert "### a" in md
        assert "### b" in md

    def test_passed_count_summary(self) -> None:
        report_pass = _make_report(name="pass")
        stats_fail = _make_stats(p95_ms=500.0)
        report_fail = _make_report(name="fail", stats=stats_fail)
        md = generate_report([report_pass, report_fail], fmt=ReportFormat.MARKDOWN)
        assert "通过场景：1 / 2" in md

    def test_scenario_report_to_dict(self) -> None:
        report = _make_report()
        d = report.to_dict()
        assert d["name"] == "test_scenario"
        assert d["stats"]["p95_ms"] == 180.0
        assert d["threshold_summary"] is not None
        assert "config" in d
        assert "timestamp" in d
