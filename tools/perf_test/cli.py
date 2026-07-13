"""性能压测 CLI 入口。

用法示例：

    # 运行所有默认场景
    python -m perf_test.cli --base-url http://localhost:8001

    # 运行指定场景
    python -m perf_test.cli --base-url http://localhost:8001 --scenario vote_query

    # 输出 JSON 格式报告到文件
    python -m perf_test.cli --base-url http://localhost:8001 --format json --output report.json

    # 自定义请求头（如 Authorization）
    python -m perf_test.cli --base-url http://localhost:8001 \\
        --header "Authorization: Bearer test-token"

退出码：
- 0：所有 blocker 阈值通过
- 1：参数错误
- 2：有 blocker 阈值失败
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Mapping

from .report import ReportFormat, ScenarioReport, generate_report
from .scenarios import (
    CONTENT_PACKAGE_DETAIL_SCENARIO,
    CONTENT_QUERY_SCENARIO,
    PLAYER_PROFILE_QUERY_SCENARIO,
    VOTE_QUERY_SCENARIO,
    VOTE_SUBMIT_SCENARIO,
    WORLD_REGION_QUERY_SCENARIO,
    Scenario,
    default_scenarios,
)
from .threshold import check_thresholds


SCENARIO_MAP: dict[str, Scenario] = {
    "vote_submit": VOTE_SUBMIT_SCENARIO,
    "vote_query": VOTE_QUERY_SCENARIO,
    "content_query": CONTENT_QUERY_SCENARIO,
    "world_region_query": WORLD_REGION_QUERY_SCENARIO,
    "player_profile_query": PLAYER_PROFILE_QUERY_SCENARIO,
    "content_package_detail": CONTENT_PACKAGE_DETAIL_SCENARIO,
}


def _parse_headers(items: list[str]) -> dict[str, str]:
    """将 ['Key: Value', ...] 转换为 dict。"""
    headers: dict[str, str] = {}
    for item in items:
        if ":" not in item:
            raise ValueError(f"无效请求头格式: {item!r}（应为 'Key: Value'）")
        key, value = item.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def _select_scenarios(name: str | None) -> list[Scenario]:
    """根据 --scenario 参数选择场景。"""
    if name is None:
        return default_scenarios()
    if name == "all":
        return default_scenarios()
    if name not in SCENARIO_MAP:
        raise ValueError(
            f"未知场景: {name!r}（可选: {', '.join(SCENARIO_MAP.keys())} 或 all）"
        )
    return [SCENARIO_MAP[name]]


async def _run_scenario(
    scenario: Scenario,
    base_url: str,
    headers: Mapping[str, str],
) -> ScenarioReport:
    """运行单个场景并返回报告。"""
    config = scenario.build_config(base_url, headers)
    from .load_runner import run_load

    stats = await run_load(config)
    summary = check_thresholds(stats, scenario.thresholds)
    return ScenarioReport(
        name=scenario.name,
        description=scenario.description,
        stats=stats,
        threshold_summary=summary,
        config={
            "base_url": config.base_url,
            "method": config.method,
            "path": config.path,
            "concurrency": config.concurrency,
            "total_requests": config.total_requests,
            "timeout_seconds": config.timeout_seconds,
        },
    )


def _build_parser() -> argparse.ArgumentParser:
    """构造 argparse 解析器。"""
    parser = argparse.ArgumentParser(
        prog="perf_test",
        description="核心接口性能压测工具（投票/内容等）",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="目标服务 base URL（如 http://localhost:8001）",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIO_MAP.keys()) + ["all"],
        default="all",
        help="选择要运行的场景（默认: all）",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="KEY: VALUE",
        help="附加请求头（可多次指定）",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in ReportFormat],
        default=ReportFormat.MARKDOWN.value,
        help="报告输出格式（默认: markdown）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="报告输出文件路径（默认: stdout）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 入口函数。

    Returns:
        退出码（0=通过，1=参数错误，2=有 blocker 阈值失败）
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        headers = _parse_headers(args.header)
    except ValueError as exc:
        print(f"参数错误: {exc}", file=sys.stderr)
        return 1

    try:
        scenarios = _select_scenarios(args.scenario)
    except ValueError as exc:
        print(f"参数错误: {exc}", file=sys.stderr)
        return 1

    # 异步运行
    reports = asyncio.run(
        _run_all(scenarios, args.base_url, headers)
    )

    # 输出报告
    fmt = ReportFormat(args.format)
    content = generate_report(reports, fmt=fmt)
    if args.output is not None:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content)

    # 退出码
    has_blocker_failure = any(
        r.threshold_summary is not None and not r.threshold_summary.passed
        for r in reports
    )
    if has_blocker_failure:
        return 2
    return 0


async def _run_all(
    scenarios: list[Scenario],
    base_url: str,
    headers: Mapping[str, str],
) -> list[ScenarioReport]:
    """运行所有场景并收集报告。"""
    reports: list[ScenarioReport] = []
    for scenario in scenarios:
        report = await _run_scenario(scenario, base_url, headers)
        reports.append(report)
    return reports


if __name__ == "__main__":
    raise SystemExit(main())
