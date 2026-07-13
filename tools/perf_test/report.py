"""压测报告生成模块。

支持两种输出格式：
- Markdown：人类可读，CI 注释 / PR 描述
- JSON：机器可读，便于 CI 解析
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .stats import LatencyStats
from .threshold import ThresholdCheckSummary


class ReportFormat(str, Enum):
    """报告输出格式。"""

    MARKDOWN = "markdown"
    JSON = "json"


@dataclass
class ScenarioReport:
    """单个场景的压测报告。"""

    name: str
    description: str
    stats: LatencyStats
    threshold_summary: ThresholdCheckSummary | None = None
    config: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。"""
        result: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "timestamp": self.timestamp,
            "config": self.config,
            "stats": self.stats.to_dict(),
        }
        if self.threshold_summary is not None:
            result["threshold_summary"] = self.threshold_summary.to_dict()
        return result


def _format_markdown_table(report: ScenarioReport) -> str:
    """将单个场景的统计指标格式化为 Markdown 表格。"""
    s = report.stats
    lines = [
        f"### {report.name}",
        "",
        f"> {report.description}",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 请求总数 | {s.count} |",
        f"| 失败数 | {s.error_count} |",
        f"| 错误率 | {s.error_rate * 100:.2f}% |",
        f"| QPS | {s.qps:.2f} |",
        f"| 耗时 | {s.duration_seconds:.2f}s |",
        f"| 最小耗时 | {s.min_ms:.2f} ms |",
        f"| 平均耗时 | {s.avg_ms:.2f} ms |",
        f"| p50 | {s.p50_ms:.2f} ms |",
        f"| p95 | {s.p95_ms:.2f} ms |",
        f"| p99 | {s.p99_ms:.2f} ms |",
        f"| 最大耗时 | {s.max_ms:.2f} ms |",
        "",
    ]
    if report.threshold_summary is not None and report.threshold_summary.results:
        lines.append("**阈值校验**：")
        lines.append("")
        lines.append("| 阈值 | 指标 | 实际值 | 上限 | 严重级别 | 结果 |")
        lines.append("|------|------|--------|------|----------|------|")
        for r in report.threshold_summary.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            lines.append(
                f"| {r.name} | {r.metric} | {r.actual:.2f} | {r.threshold:.2f} | {r.severity} | {status} |"
            )
        overall = "✅ 全部通过" if report.threshold_summary.passed else "❌ 有 blocker 失败"
        lines.append("")
        lines.append(f"**总体**：{overall}")
        lines.append("")
    return "\n".join(lines)


def _report_to_markdown(reports: list[ScenarioReport]) -> str:
    """将场景报告列表渲染为完整 Markdown 报告。"""
    lines = [
        "# 性能压测报告",
        "",
        f"> 生成时间：{datetime.now(timezone.utc).isoformat()}",
        "",
        f"> 场景数：{len(reports)}",
        "",
    ]
    passed = sum(
        1
        for r in reports
        if r.threshold_summary is None or r.threshold_summary.passed
    )
    lines.append(f"> 通过场景：{passed} / {len(reports)}")
    lines.append("")
    for r in reports:
        lines.append(_format_markdown_table(r))
    return "\n".join(lines)


def _report_to_json(reports: list[ScenarioReport]) -> str:
    """将场景报告列表渲染为 JSON 字符串。"""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario_count": len(reports),
        "scenarios": [r.to_dict() for r in reports],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def generate_report(
    reports: list[ScenarioReport],
    fmt: ReportFormat = ReportFormat.MARKDOWN,
) -> str:
    """生成压测报告。

    Args:
        reports: 场景报告列表
        fmt: 输出格式

    Returns:
        报告字符串
    """
    if fmt == ReportFormat.JSON:
        return _report_to_json(reports)
    return _report_to_markdown(reports)
