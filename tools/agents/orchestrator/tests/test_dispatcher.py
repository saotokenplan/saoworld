from unittest.mock import MagicMock
from pydantic import BaseModel

from ..dispatcher import AgentDispatcher, AgentExecutionResult


class SampleOutput(BaseModel):
    """测试用输出模型"""
    name: str = "test"
    value: int = 42


class TestAgentDispatcher:
    """AgentDispatcher 单元测试"""

    def test_init(self):
        dispatcher = AgentDispatcher()
        assert len(dispatcher.AGENT_REGISTRY) == 11
        assert "product-agent" in dispatcher.AGENT_REGISTRY
        assert "system-designer-agent" in dispatcher.AGENT_REGISTRY
        assert "backend-agent" in dispatcher.AGENT_REGISTRY
        assert "gameplay-agent" in dispatcher.AGENT_REGISTRY
        assert "world-agent" in dispatcher.AGENT_REGISTRY
        assert "world-agent-requirement" in dispatcher.AGENT_REGISTRY
        assert "qa-agent" in dispatcher.AGENT_REGISTRY
        assert "build-agent" in dispatcher.AGENT_REGISTRY
        assert "ops-agent" in dispatcher.AGENT_REGISTRY
        assert "ops-agent-insight" in dispatcher.AGENT_REGISTRY
        assert "ops-agent-requirement" in dispatcher.AGENT_REGISTRY

    def test_is_agent_registered(self):
        dispatcher = AgentDispatcher()
        assert dispatcher.is_agent_registered("product-agent")
        assert dispatcher.is_agent_registered("backend-agent")
        assert not dispatcher.is_agent_registered("unknown-agent")

    def test_get_registered_agents(self):
        dispatcher = AgentDispatcher()
        agents = dispatcher.get_registered_agents()
        assert "product-agent" in agents
        assert len(agents) == 11

    def test_dispatch_unregistered_agent(self):
        dispatcher = AgentDispatcher()
        result = dispatcher.dispatch("unknown-agent", task_id="T-001")
        assert not result.success
        assert "未注册" in result.error
        assert result.task_id == "T-001"

    def test_dispatch_agent_import_failure(self):
        dispatcher = AgentDispatcher()
        # 修改注册表中的模块路径为不存在的路径
        original_module = dispatcher.AGENT_REGISTRY["product-agent"]["module"]
        dispatcher.AGENT_REGISTRY["product-agent"]["module"] = "nonexistent.module"

        result = dispatcher.dispatch("product-agent", task_id="T-002")
        assert not result.success
        assert "实例化失败" in result.error

        # 恢复
        dispatcher.AGENT_REGISTRY["product-agent"]["module"] = original_module
        dispatcher.reset()

    def test_dispatch_with_mock_agent(self):
        dispatcher = AgentDispatcher()

        # 创建 mock agent
        mock_agent = MagicMock()
        mock_agent.run.return_value = {"version": "0.2.0", "tasks": []}

        # 直接注入 mock 实例
        dispatcher._agent_instances["mock-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["mock-agent"] = {
            "module": "mock",
            "class": "MockAgent",
            "method": "run",
        }

        result = dispatcher.dispatch("mock-agent", task_id="T-003")
        assert result.success
        assert result.output == {"version": "0.2.0", "tasks": []}
        mock_agent.run.assert_called_once()

        # 清理
        del dispatcher.AGENT_REGISTRY["mock-agent"]

    def test_dispatch_with_mock_agent_and_input(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock()
        mock_agent.execute.return_value = SampleOutput(name="result", value=100)

        dispatcher._agent_instances["test-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["test-agent"] = {
            "module": "test",
            "class": "TestAgent",
            "method": "execute",
        }

        result = dispatcher.dispatch(
            "test-agent",
            task_input={"key": "value"},
            task_id="T-004",
        )
        assert result.success
        assert result.output["name"] == "result"
        assert result.output["value"] == 100
        mock_agent.execute.assert_called_once_with(key="value")

        del dispatcher.AGENT_REGISTRY["test-agent"]

    def test_dispatch_agent_exception(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock()
        mock_agent.run.side_effect = ValueError("测试异常")

        dispatcher._agent_instances["fail-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["fail-agent"] = {
            "module": "fail",
            "class": "FailAgent",
            "method": "run",
        }

        result = dispatcher.dispatch("fail-agent", task_id="T-005")
        assert not result.success
        assert "测试异常" in result.error

        del dispatcher.AGENT_REGISTRY["fail-agent"]

    def test_dispatch_agent_missing_method(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock(spec=[])  # 没有方法的 mock

        dispatcher._agent_instances["no-method-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["no-method-agent"] = {
            "module": "no_method",
            "class": "NoMethodAgent",
            "method": "nonexistent_method",
        }

        result = dispatcher.dispatch("no-method-agent", task_id="T-006")
        assert not result.success
        assert "没有方法" in result.error

        del dispatcher.AGENT_REGISTRY["no-method-agent"]

    def test_reset(self):
        dispatcher = AgentDispatcher()
        dispatcher._agent_instances["test"] = MagicMock()
        dispatcher._agent_classes["test"] = object

        dispatcher.reset()

        assert len(dispatcher._agent_instances) == 0
        assert len(dispatcher._agent_classes) == 0

    def test_dispatch_dict_return(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock()
        mock_agent.run.return_value = {"key": "dict_value"}

        dispatcher._agent_instances["dict-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["dict-agent"] = {
            "module": "dict",
            "class": "DictAgent",
            "method": "run",
        }

        result = dispatcher.dispatch("dict-agent", task_id="T-007")
        assert result.success
        assert result.output == {"key": "dict_value"}

        del dispatcher.AGENT_REGISTRY["dict-agent"]

    def test_dispatch_none_return(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock()
        mock_agent.run.return_value = None

        dispatcher._agent_instances["none-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["none-agent"] = {
            "module": "none",
            "class": "NoneAgent",
            "method": "run",
        }

        result = dispatcher.dispatch("none-agent", task_id="T-008")
        assert result.success
        assert result.output == {}

        del dispatcher.AGENT_REGISTRY["none-agent"]

    def test_execution_result_model(self):
        result = AgentExecutionResult(
            task_id="T-001",
            agent="test-agent",
            success=True,
            output={"key": "value"},
            duration_ms=100,
        )
        assert result.task_id == "T-001"
        assert result.success
        assert result.output["key"] == "value"
        assert result.error is None

    def test_dispatch_duration_tracked(self):
        dispatcher = AgentDispatcher()

        mock_agent = MagicMock()
        mock_agent.run.return_value = {"result": True}

        dispatcher._agent_instances["time-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["time-agent"] = {
            "module": "time",
            "class": "TimeAgent",
            "method": "run",
        }

        result = dispatcher.dispatch("time-agent", task_id="T-009")
        assert result.success
        assert result.duration_ms >= 0

        del dispatcher.AGENT_REGISTRY["time-agent"]
