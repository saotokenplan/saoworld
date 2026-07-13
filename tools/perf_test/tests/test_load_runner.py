"""load_runner 模块单元测试。

使用 respx/httpx-mock 思路，但为了不引入新依赖，改为直接通过 httpx + aiohttp
不可用环境时使用 httpx MockTransport。
"""

from typing import Any

import pytest

import httpx

from perf_test.load_runner import LoadConfig, LoadRunner, run_load


def _make_handler(
    status: int = 200,
    delay_seconds: float = 0.0,
    body: bytes = b'{"ok": true}',
) -> httpx.MockTransport:
    """构造一个 httpx MockTransport。"""

    def handler(request: httpx.Request) -> httpx.Response:
        if delay_seconds > 0:
            import time

            time.sleep(delay_seconds)
        return httpx.Response(status, content=body)

    return httpx.MockTransport(handler)


def _patched_async_client_init(transport: httpx.MockTransport) -> Any:
    """返回一个 monkey-patch 函数，把 transport 注入 httpx.AsyncClient.__init__。

    返回的 callable 接受 (self, *args, **kwargs) 并自动注入 transport。
    调用方需要在使用前保存原 __init__，使用后恢复。
    """
    original_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: Any, **kwargs: Any) -> None:
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    return patched_init, original_init


class TestLoadRunner:
    """LoadRunner 行为测试。"""

    @pytest.mark.asyncio
    async def test_basic_get(self) -> None:
        transport = _make_handler(status=200)
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/api/v1/test",
            concurrency=2,
            total_requests=10,
            timeout_seconds=5.0,
        )
        runner = LoadRunner(config)
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            stats = await runner.run()
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        assert stats.count == 10
        assert stats.error_count == 0
        assert stats.error_rate == 0.0
        assert stats.qps > 0

    @pytest.mark.asyncio
    async def test_error_status_counts_as_error(self) -> None:
        transport = _make_handler(status=500)
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/api/v1/test",
            concurrency=2,
            total_requests=5,
        )
        runner = LoadRunner(config)
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            stats = await runner.run()
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        assert stats.count == 5
        assert stats.error_count == 5
        assert stats.error_rate == 1.0

    @pytest.mark.asyncio
    async def test_warmup_not_counted(self) -> None:
        # warmup 应该被发送但不影响统计
        transport = _make_handler(status=200)
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/api/v1/test",
            concurrency=2,
            total_requests=5,
            warmup_requests=3,
        )
        runner = LoadRunner(config)
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            stats = await runner.run()
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        # warmup 不计入统计
        assert stats.count == 5

    @pytest.mark.asyncio
    async def test_timeout_handled(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("simulated timeout")

        transport = httpx.MockTransport(handler)
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/api/v1/test",
            concurrency=1,
            total_requests=3,
            timeout_seconds=0.1,
        )
        runner = LoadRunner(config)
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            stats = await runner.run()
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        assert stats.count == 3
        assert stats.error_count == 3
        assert stats.error_rate == 1.0

    @pytest.mark.asyncio
    async def test_run_load_helper(self) -> None:
        transport = _make_handler(status=200)
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/test",
            concurrency=2,
            total_requests=4,
        )
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            stats = await run_load(config)
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        assert stats.count == 4
        assert stats.error_count == 0

    @pytest.mark.asyncio
    async def test_dynamic_path(self) -> None:
        # 验证 path_factory 工作正常
        config = LoadConfig(
            base_url="http://testserver",
            method="GET",
            path="/default",
            path_factory=lambda i: f"/dynamic/{i}",
            concurrency=1,
            total_requests=3,
        )
        runner = LoadRunner(config)

        seen_paths: list[str] = []

        async def capturing_handler(request: httpx.Request) -> httpx.Response:
            seen_paths.append(request.url.path)
            return httpx.Response(200, content=b"{}")

        transport = httpx.MockTransport(capturing_handler)
        patched, original_init = _patched_async_client_init(transport)
        httpx.AsyncClient.__init__ = patched  # type: ignore[method-assign]
        try:
            await runner.run()
        finally:
            httpx.AsyncClient.__init__ = original_init  # type: ignore[method-assign]

        assert seen_paths == ["/dynamic/0", "/dynamic/1", "/dynamic/2"]
