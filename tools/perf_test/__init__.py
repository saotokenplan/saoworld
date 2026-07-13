"""性能压测工具（Performance Testing Toolkit）。

为投票、内容等核心接口提供：
- 异步负载执行（httpx + asyncio.Semaphore）
- 统计指标计算（p50 / p95 / p99 / qps）
- 阈值校验（投票提交 p95 < 300ms、查询 p95 < 100ms）
- Markdown / JSON 报告生成
- 内置核心接口场景（vote_submit / vote_query / content_query）
- CLI 命令行入口

不引入 locust / wrk / vegeta 等外部压测框架，仅使用标准库 + httpx。
"""

from .stats import LatencyStats, compute_stats
from .load_runner import LoadConfig, LoadRunner, RequestResult
from .threshold import Threshold, ThresholdResult, check_thresholds
from .report import ReportFormat, generate_report
from .scenarios import (
    Scenario,
    content_query_scenario,
    vote_query_scenario,
    vote_submit_scenario,
    default_scenarios,
)

__all__ = [
    "LatencyStats",
    "compute_stats",
    "LoadConfig",
    "LoadRunner",
    "RequestResult",
    "Threshold",
    "ThresholdResult",
    "check_thresholds",
    "ReportFormat",
    "generate_report",
    "Scenario",
    "content_query_scenario",
    "vote_query_scenario",
    "vote_submit_scenario",
    "default_scenarios",
]

__version__ = "0.1.0"
