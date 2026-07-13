"""cli 模块单元测试。"""

from pathlib import Path

import pytest

from perf_test.cli import _parse_headers, _select_scenarios, main, _build_parser


class TestParseHeaders:
    """请求头解析测试。"""

    def test_single_header(self) -> None:
        h = _parse_headers(["Authorization: Bearer xxx"])
        assert h == {"Authorization": "Bearer xxx"}

    def test_multiple_headers(self) -> None:
        h = _parse_headers([
            "Authorization: Bearer xxx",
            "X-Trace-Id: trace-1",
        ])
        assert h["Authorization"] == "Bearer xxx"
        assert h["X-Trace-Id"] == "trace-1"

    def test_value_with_colon(self) -> None:
        h = _parse_headers(["X-Time: 12:34:56"])
        assert h["X-Time"] == "12:34:56"

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="无效请求头格式"):
            _parse_headers(["InvalidNoColon"])


class TestSelectScenarios:
    """场景选择测试。"""

    def test_none_returns_default(self) -> None:
        scenarios = _select_scenarios(None)
        assert len(scenarios) == 3

    def test_all_returns_default(self) -> None:
        scenarios = _select_scenarios("all")
        assert len(scenarios) == 3

    def test_specific_scenario(self) -> None:
        scenarios = _select_scenarios("vote_query")
        assert len(scenarios) == 1
        assert scenarios[0].name == "vote_query"

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="未知场景"):
            _select_scenarios("unknown_scenario")


class TestBuildParser:
    """argparse 解析器测试。"""

    def test_required_base_url(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_full_args(self) -> None:
        parser = _build_parser()
        args = parser.parse_args([
            "--base-url", "http://x",
            "--scenario", "vote_query",
            "--format", "json",
            "--output", "/tmp/r.json",
        ])
        assert args.base_url == "http://x"
        assert args.scenario == "vote_query"
        assert args.format == "json"
        assert args.output == Path("/tmp/r.json")


class TestMain:
    """main 函数行为测试。"""

    def test_main_invalid_header_returns_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["--base-url", "http://x", "--header", "badformat"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "参数错误" in captured.err

    def test_main_missing_base_url_returns_2(self) -> None:
        # argparse 直接对 --base-url 必填项触发 SystemExit(2)
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_main_invalid_scenario_raises_or_returns_error(self) -> None:
        # argparse 会在 choices 不匹配时触发 SystemExit(2)
        with pytest.raises(SystemExit) as exc_info:
            main(["--base-url", "http://x", "--scenario", "unknown"])
        assert exc_info.value.code == 2
