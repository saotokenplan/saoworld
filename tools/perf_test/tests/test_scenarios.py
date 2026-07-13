"""scenarios 模块单元测试。"""

from perf_test.scenarios import (
    CONTENT_QUERY_SCENARIO,
    VOTE_QUERY_SCENARIO,
    VOTE_SUBMIT_SCENARIO,
    default_scenarios,
    vote_query_scenario,
    vote_submit_scenario,
    content_query_scenario,
)


class TestScenarios:
    """场景工厂函数测试。"""

    def test_vote_submit_scenario(self) -> None:
        config = vote_submit_scenario("http://localhost:8001", {})
        assert config.base_url == "http://localhost:8001"
        assert config.method == "POST"
        assert config.path == "/api/v1/votes/submit"
        assert config.concurrency >= 1
        assert config.total_requests >= 1
        assert config.body_factory is not None

    def test_vote_query_scenario(self) -> None:
        config = vote_query_scenario("http://localhost:8001", {})
        assert config.method == "GET"
        assert config.path == "/api/v1/votes/current"
        assert config.concurrency >= 1
        assert config.total_requests >= 1

    def test_content_query_scenario(self) -> None:
        config = content_query_scenario("http://localhost:8001", {})
        assert config.method == "GET"
        assert config.path == "/api/v1/content/updates"
        assert config.concurrency >= 1
        assert config.total_requests >= 1

    def test_headers_are_passed_through(self) -> None:
        config = vote_query_scenario("http://localhost:8001", {"Authorization": "Bearer x"})
        assert config.headers == {"Authorization": "Bearer x"}

    def test_default_scenarios_returns_three(self) -> None:
        scenarios = default_scenarios()
        assert len(scenarios) == 3
        names = {s.name for s in scenarios}
        assert names == {"vote_submit", "vote_query", "content_query"}

    def test_scenarios_have_thresholds(self) -> None:
        for s in (VOTE_SUBMIT_SCENARIO, VOTE_QUERY_SCENARIO, CONTENT_QUERY_SCENARIO):
            assert len(s.thresholds) > 0
            p95 = next((t for t in s.thresholds if t.metric == "p95_ms"), None)
            assert p95 is not None
            assert p95.max_value > 0

    def test_scenario_build_config(self) -> None:
        config = VOTE_QUERY_SCENARIO.build_config("http://x", {"K": "V"})
        assert config.base_url == "http://x"
        assert config.headers == {"K": "V"}

    def test_vote_submit_body_factory_unique(self) -> None:
        # 不同 i 应当可以生成不同的请求体（验证幂等性 + 玩家区分）
        config = vote_submit_scenario("http://x", {})
        assert config.body_factory is not None
        bodies = [config.body_factory(i) for i in range(5)]
        # 不同 i 至少 device_fingerprint 不同
        fps = {b["device_fingerprint_hash"] for b in bodies}
        assert len(fps) == 5
