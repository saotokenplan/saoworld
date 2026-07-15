"""核心接口压测场景。

每个场景是一个工厂函数：接收 (base_url, headers) 返回 LoadConfig。

内置场景：
- vote_submit_scenario：投票提交（POST /api/v1/votes/submit）
- vote_query_scenario：投票查询（GET /api/v1/votes/current）
- content_query_scenario：内容查询（GET /api/v1/content/updates）
- world_region_query_scenario：世界区域查询（GET /api/v1/world/regions）
- player_profile_query_scenario：玩家档案查询（GET /api/v1/player/profile）
- content_package_detail_scenario：内容包详情查询（GET /api/v1/content/packages/{id}）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable, Mapping

from .load_runner import LoadConfig
from .threshold import Threshold, get_default_thresholds


@dataclass
class Scenario:
    """压测场景定义。"""

    name: str
    description: str
    config_factory: Callable[[str, Mapping[str, str]], LoadConfig]
    thresholds: list[Threshold]

    def build_config(
        self,
        base_url: str,
        headers: Mapping[str, str] | None = None,
    ) -> LoadConfig:
        """构造 LoadConfig。"""
        return self.config_factory(base_url, headers or {})


def _idempotency_key(i: int) -> str:
    return f"perf_{uuid.uuid4().hex}"


def vote_submit_scenario(
    base_url: str,
    headers: Mapping[str, str],
    candidate_id: str = "00000000-0000-0000-0000-000000000001",
) -> LoadConfig:
    """投票提交场景（POST /api/v1/votes/submit）。

    默认配置：并发 10，总数 50，每次提交使用新 player_id / idempotency_key。
    """
    return LoadConfig(
        base_url=base_url,
        method="POST",
        path="/api/v1/votes/submit",
        concurrency=10,
        total_requests=50,
        timeout_seconds=10.0,
        headers=dict(headers),
        body_factory=lambda i: {
            "candidate_id": candidate_id,
            "device_fingerprint_hash": f"perf_device_{i}",
            "weight": 1.0,
        },
    )


def vote_query_scenario(
    base_url: str,
    headers: Mapping[str, str],
) -> LoadConfig:
    """投票查询场景（GET /api/v1/votes/current）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path="/api/v1/votes/current",
        concurrency=20,
        total_requests=100,
        timeout_seconds=5.0,
        headers=dict(headers),
    )


def content_query_scenario(
    base_url: str,
    headers: Mapping[str, str],
) -> LoadConfig:
    """内容查询场景（GET /api/v1/content/updates）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path="/api/v1/content/updates",
        concurrency=20,
        total_requests=100,
        timeout_seconds=5.0,
        headers=dict(headers),
    )


def world_region_query_scenario(
    base_url: str,
    headers: Mapping[str, str],
) -> LoadConfig:
    """世界区域查询场景（GET /api/v1/world/regions）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path="/api/v1/world/regions",
        concurrency=20,
        total_requests=100,
        timeout_seconds=5.0,
        headers=dict(headers),
    )


def player_profile_query_scenario(
    base_url: str,
    headers: Mapping[str, str],
) -> LoadConfig:
    """玩家档案查询场景（GET /api/v1/player/profile）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path="/api/v1/player/profile",
        concurrency=10,
        total_requests=50,
        timeout_seconds=5.0,
        headers=dict(headers),
    )


def content_package_detail_scenario(
    base_url: str,
    headers: Mapping[str, str],
    package_id: str = "00000000-0000-0000-0000-000000000001",
) -> LoadConfig:
    """内容包详情查询场景（GET /api/v1/content/packages/{id}）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path=f"/api/v1/content/packages/{package_id}",
        concurrency=20,
        total_requests=100,
        timeout_seconds=5.0,
        headers=dict(headers),
    )


VOTE_SUBMIT_SCENARIO = Scenario(
    name="vote_submit",
    description="投票提交接口：POST /api/v1/votes/submit，要求 p95 < 300ms",
    config_factory=vote_submit_scenario,
    thresholds=get_default_thresholds("vote_submit"),
)

VOTE_QUERY_SCENARIO = Scenario(
    name="vote_query",
    description="投票查询接口：GET /api/v1/votes/current，要求 p95 < 100ms",
    config_factory=vote_query_scenario,
    thresholds=get_default_thresholds("vote_query"),
)

CONTENT_QUERY_SCENARIO = Scenario(
    name="content_query",
    description="内容查询接口：GET /api/v1/content/updates，要求 p95 < 100ms",
    config_factory=content_query_scenario,
    thresholds=get_default_thresholds("content_query"),
)

WORLD_REGION_QUERY_SCENARIO = Scenario(
    name="world_region_query",
    description="世界区域查询接口：GET /api/v1/world/regions，要求 p95 < 100ms",
    config_factory=world_region_query_scenario,
    thresholds=get_default_thresholds("world_region_query"),
)

PLAYER_PROFILE_QUERY_SCENARIO = Scenario(
    name="player_profile_query",
    description="玩家档案查询接口：GET /api/v1/player/profile，要求 p95 < 200ms",
    config_factory=player_profile_query_scenario,
    thresholds=get_default_thresholds("player_profile_query"),
)

CONTENT_PACKAGE_DETAIL_SCENARIO = Scenario(
    name="content_package_detail",
    description="内容包详情查询接口：GET /api/v1/content/packages/{id}，要求 p95 < 100ms",
    config_factory=content_package_detail_scenario,
    thresholds=get_default_thresholds("content_package_detail"),
)


def vote_submit_high_concurrency_scenario(
    base_url: str,
    headers: Mapping[str, str],
    candidate_id: str = "00000000-0000-0000-0000-000000000001",
) -> LoadConfig:
    """高并发投票提交场景（1000 并发）。"""
    return LoadConfig(
        base_url=base_url,
        method="POST",
        path="/api/v1/votes/submit",
        concurrency=100,
        total_requests=10000,
        timeout_seconds=30.0,
        headers=dict(headers),
        body_factory=lambda i: {
            "candidate_id": candidate_id,
            "device_fingerprint_hash": f"perf_device_{i}",
            "weight": 1.0,
        },
    )


def query_high_concurrency_scenario(
    base_url: str,
    headers: Mapping[str, str],
) -> LoadConfig:
    """高并发查询场景（5000 并发）。"""
    return LoadConfig(
        base_url=base_url,
        method="GET",
        path="/api/v1/votes/current",
        concurrency=200,
        total_requests=50000,
        timeout_seconds=30.0,
        headers=dict(headers),
    )


VOTE_SUBMIT_HIGH_CONCURRENCY_SCENARIO = Scenario(
    name="vote_submit_high",
    description="高并发投票提交：1000 并发，要求 p95 < 300ms",
    config_factory=vote_submit_high_concurrency_scenario,
    thresholds=get_default_thresholds("vote_submit_high"),
)

QUERY_HIGH_CONCURRENCY_SCENARIO = Scenario(
    name="query_high",
    description="高并发查询：5000 并发，要求 p95 < 500ms",
    config_factory=query_high_concurrency_scenario,
    thresholds=get_default_thresholds("query_high"),
)


def default_scenarios() -> list[Scenario]:
    """获取默认场景列表。"""
    return [
        VOTE_SUBMIT_SCENARIO,
        VOTE_QUERY_SCENARIO,
        CONTENT_QUERY_SCENARIO,
        WORLD_REGION_QUERY_SCENARIO,
        PLAYER_PROFILE_QUERY_SCENARIO,
        CONTENT_PACKAGE_DETAIL_SCENARIO,
    ]
