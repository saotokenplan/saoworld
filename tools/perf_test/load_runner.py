"""异步负载执行器。

使用 httpx.AsyncClient + asyncio.Semaphore 控制并发数，
对单个场景执行 N 次请求并收集每次请求的响应耗时与状态码。
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import httpx

from .stats import LatencyStats, compute_stats


@dataclass
class RequestResult:
    """单次请求的执行结果。"""

    success: bool
    latency_ms: float
    status_code: int
    error: str | None = None


@dataclass
class LoadConfig:
    """负载执行配置。"""

    base_url: str
    method: str = "GET"
    path: str = "/"
    concurrency: int = 10
    total_requests: int = 100
    timeout_seconds: float = 30.0
    headers: Mapping[str, str] = field(default_factory=dict)
    json_body: dict[str, Any] | None = None
    # 可选：每个请求的 query 参数动态生成函数
    query_params_factory: Callable[[int], dict[str, str]] | None = None
    # 可选：每个请求的 path 参数动态生成函数
    path_factory: Callable[[int], str] | None = None
    # 可选：每个请求的 json body 动态生成函数
    body_factory: Callable[[int], dict[str, Any]] | None = None
    # 可选：warm-up 数量（不计入统计）
    warmup_requests: int = 0


class LoadRunner:
    """异步负载执行器。"""

    def __init__(self, config: LoadConfig) -> None:
        self._config = config

    async def _execute_one(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        request_index: int,
    ) -> RequestResult:
        """执行单次 HTTP 请求。"""
        method = self._config.method
        path = self._config.path_factory(request_index) if self._config.path_factory else self._config.path
        url = f"{self._config.base_url.rstrip('/')}{path}"
        body = self._config.body_factory(request_index) if self._config.body_factory else self._config.json_body
        params = self._config.query_params_factory(request_index) if self._config.query_params_factory else None

        # 合并请求头
        headers = dict(self._config.headers)
        # 自动注入请求 ID（如果未设置）
        if "X-Request-Id" not in headers and "x-request-id" not in {h.lower() for h in headers}:
            headers["X-Request-Id"] = f"req_perf_{uuid.uuid4().hex[:12]}"

        async with semaphore:
            start = time.perf_counter()
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    json=body,
                    params=params,
                    headers=headers,
                    timeout=self._config.timeout_seconds,
                )
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                success = 200 <= response.status_code < 400
                return RequestResult(
                    success=success,
                    latency_ms=elapsed_ms,
                    status_code=response.status_code,
                    error=None if success else f"HTTP {response.status_code}",
                )
            except httpx.TimeoutException as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return RequestResult(
                    success=False,
                    latency_ms=elapsed_ms,
                    status_code=0,
                    error=f"timeout: {exc}",
                )
            except httpx.HTTPError as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return RequestResult(
                    success=False,
                    latency_ms=elapsed_ms,
                    status_code=0,
                    error=f"http_error: {exc}",
                )
            except Exception as exc:  # noqa: BLE001
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return RequestResult(
                    success=False,
                    latency_ms=elapsed_ms,
                    status_code=0,
                    error=f"unexpected: {exc}",
                )

    async def run(self) -> LatencyStats:
        """执行负载测试并返回统计结果。"""
        semaphore = asyncio.Semaphore(self._config.concurrency)
        total = self._config.total_requests
        warmup = self._config.warmup_requests

        async with httpx.AsyncClient() as client:
            # Warm-up（不计入统计）
            if warmup > 0:
                warmup_tasks = [
                    self._execute_one(client, semaphore, -i - 1) for i in range(warmup)
                ]
                await asyncio.gather(*warmup_tasks)

            # 正式压测
            start = time.perf_counter()
            tasks = [
                self._execute_one(client, semaphore, i) for i in range(total)
            ]
            results = await asyncio.gather(*tasks)
            duration = time.perf_counter() - start

        latencies = [r.latency_ms for r in results if r.success]
        errors = sum(1 for r in results if not r.success)
        return compute_stats(latencies, error_count=errors, duration_seconds=duration)


async def run_load(
    config: LoadConfig,
) -> LatencyStats:
    """便捷函数：执行一次负载测试。"""
    runner = LoadRunner(config)
    return await runner.run()


# 类型别名：场景工厂
ScenarioFactory = Callable[[str, Mapping[str, str]], LoadConfig]
