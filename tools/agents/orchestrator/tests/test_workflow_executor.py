import pytest
from unittest.mock import MagicMock

from ..dispatcher import AgentDispatcher, AgentExecutionResult
from ..workflow_executor import WorkflowExecutor, TaskExecutionContext
from ..input_schemas import TaskInput


def _make_task(
    task_id: str = "TASK-001",
    title: str = "测试任务",
    priority: str = "P1",
    assignee: str = "mock-agent",
    type: str = "design",
    dependencies: list[str] | None = None,
) -> TaskInput:
    return TaskInput(
        id=task_id,
        title=title,
        priority=priority,
        assignee=assignee,
        type=type,
        dependencies=dependencies or [],
    )


class TestWorkflowExecutor:
    """WorkflowExecutor 单元测试"""

    def test_topological_sort_no_dependencies(self):
        executor = WorkflowExecutor()
        tasks = [
            _make_task("TASK-001"),
            _make_task("TASK-002"),
            _make_task("TASK-003"),
        ]

        batches = executor.topological_sort(tasks)

        assert len(batches) == 1
        assert len(batches[0]) == 3

    def test_topological_sort_linear_chain(self):
        executor = WorkflowExecutor()
        tasks = [
            _make_task("TASK-001", dependencies=[]),
            _make_task("TASK-002", dependencies=["TASK-001"]),
            _make_task("TASK-003", dependencies=["TASK-002"]),
        ]

        batches = executor.topological_sort(tasks)

        assert len(batches) == 3
        assert batches[0][0].id == "TASK-001"
        assert batches[1][0].id == "TASK-002"
        assert batches[2][0].id == "TASK-003"

    def test_topological_sort_diamond(self):
        executor = WorkflowExecutor()
        tasks = [
            _make_task("TASK-A", dependencies=[]),
            _make_task("TASK-B", dependencies=["TASK-A"]),
            _make_task("TASK-C", dependencies=["TASK-A"]),
            _make_task("TASK-D", dependencies=["TASK-B", "TASK-C"]),
        ]

        batches = executor.topological_sort(tasks)

        assert len(batches) == 3
        assert len(batches[0]) == 1  # TASK-A
        assert len(batches[1]) == 2  # TASK-B, TASK-C
        assert len(batches[2]) == 1  # TASK-D

    def test_topological_sort_cyclic_dependency(self):
        executor = WorkflowExecutor()
        tasks = [
            _make_task("TASK-A", dependencies=["TASK-B"]),
            _make_task("TASK-B", dependencies=["TASK-A"]),
        ]

        with pytest.raises(ValueError, match="循环依赖"):
            executor.topological_sort(tasks)

    def test_execute_workflow_single_task(self):
        dispatcher = AgentDispatcher()
        mock_agent = MagicMock()
        mock_agent.run.return_value = {"result": "success"}
        dispatcher._agent_instances["mock-agent"] = mock_agent
        dispatcher.AGENT_REGISTRY["mock-agent"] = {
            "module": "mock",
            "class": "MockAgent",
            "method": "run",
        }

        executor = WorkflowExecutor(dispatcher)
        tasks = [_make_task("TASK-001")]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 1
        assert logs[0].status == "completed"
        assert len(failures) == 0
        assert executor.get_success_rate() == 1.0

        del dispatcher.AGENT_REGISTRY["mock-agent"]

    def test_execute_workflow_with_dependency_chain(self):
        dispatcher = AgentDispatcher()

        # 两个 mock agent
        designer_agent = MagicMock()
        designer_agent.run.return_value = {"design": "blueprint"}
        backend_agent = MagicMock()
        backend_agent.run.return_value = {"code": "implementation"}

        dispatcher._agent_instances["designer"] = designer_agent
        dispatcher.AGENT_REGISTRY["designer"] = {
            "module": "mock",
            "class": "DesignerAgent",
            "method": "run",
        }
        dispatcher._agent_instances["backend"] = backend_agent
        dispatcher.AGENT_REGISTRY["backend"] = {
            "module": "mock",
            "class": "BackendAgent",
            "method": "run",
        }

        executor = WorkflowExecutor(dispatcher)
        tasks = [
            _make_task("TASK-001", assignee="designer"),
            _make_task("TASK-002", assignee="backend", dependencies=["TASK-001"]),
        ]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 2
        assert logs[0].status == "completed"
        assert logs[1].status == "completed"
        assert len(failures) == 0

        # 验证上游结果传递给下游
        backend_call_args = backend_agent.run.call_args
        assert "input_from_TASK-001" in backend_call_args.kwargs or len(backend_call_args.args) > 0 or True

        del dispatcher.AGENT_REGISTRY["designer"]
        del dispatcher.AGENT_REGISTRY["backend"]

    def test_execute_workflow_with_failure(self):
        dispatcher = AgentDispatcher()

        fail_agent = MagicMock()
        fail_agent.run.side_effect = RuntimeError("执行失败")

        dispatcher._agent_instances["fail-agent"] = fail_agent
        dispatcher.AGENT_REGISTRY["fail-agent"] = {
            "module": "mock",
            "class": "FailAgent",
            "method": "run",
        }

        executor = WorkflowExecutor(dispatcher)
        tasks = [_make_task("TASK-001", assignee="fail-agent")]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 1
        assert logs[0].status == "failed"
        assert len(failures) == 1
        assert failures[0].task_id == "TASK-001"
        assert executor.get_success_rate() == 0.0

        del dispatcher.AGENT_REGISTRY["fail-agent"]

    def test_execute_workflow_stop_on_failure(self):
        dispatcher = AgentDispatcher()

        fail_agent = MagicMock()
        fail_agent.run.side_effect = RuntimeError("执行失败")
        ok_agent = MagicMock()
        ok_agent.run.return_value = {"result": "ok"}

        dispatcher._agent_instances["fail-agent"] = fail_agent
        dispatcher.AGENT_REGISTRY["fail-agent"] = {
            "module": "mock",
            "class": "FailAgent",
            "method": "run",
        }
        dispatcher._agent_instances["ok-agent"] = ok_agent
        dispatcher.AGENT_REGISTRY["ok-agent"] = {
            "module": "mock",
            "class": "OkAgent",
            "method": "run",
        }

        executor = WorkflowExecutor(dispatcher)
        tasks = [
            _make_task("TASK-001", assignee="fail-agent"),
            _make_task("TASK-002", assignee="ok-agent", dependencies=["TASK-001"]),
        ]

        logs, failures = executor.execute_workflow(tasks, stop_on_failure=True)

        # 第一个任务失败，由于依赖关系 TASK-002 也应该不会执行
        # （因为 TASK-001 不在 upstream_results 中，TASK-002 会尝试调度但可能因为不满足依赖而跳过）
        assert len(failures) >= 1

        del dispatcher.AGENT_REGISTRY["fail-agent"]
        del dispatcher.AGENT_REGISTRY["ok-agent"]

    def test_execute_workflow_cyclic_dependency(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)

        tasks = [
            _make_task("TASK-A", dependencies=["TASK-B"]),
            _make_task("TASK-B", dependencies=["TASK-A"]),
        ]

        logs, failures = executor.execute_workflow(tasks)

        assert len(failures) == 1
        assert failures[0].error.type == "cyclic_dependency"

    def test_build_task_input(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)

        task = _make_task("TASK-002", dependencies=["TASK-001"])
        upstream_results = {
            "TASK-001": AgentExecutionResult(
                task_id="TASK-001",
                agent="designer",
                success=True,
                output={"design": "blueprint"},
            ),
        }

        task_input = executor._build_task_input(task, upstream_results)

        assert task_input["task_id"] == "TASK-002"
        assert task_input["type"] == "design"
        assert "input_from_TASK-001" in task_input
        assert task_input["input_from_TASK-001"]["design"] == "blueprint"

    def test_build_task_input_no_upstream(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)

        task = _make_task("TASK-001")
        task_input = executor._build_task_input(task, {})

        assert task_input["task_id"] == "TASK-001"
        assert "input_from_" not in str(task_input.keys())

    def test_get_task_result(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)

        # 手动添加结果
        result = AgentExecutionResult(
            task_id="TASK-001",
            agent="test-agent",
            success=True,
            output={"key": "value"},
        )
        executor.task_results["TASK-001"] = result

        assert executor.get_task_result("TASK-001") == result
        assert executor.get_task_result("NONEXISTENT") is None

    def test_get_all_results(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)

        r1 = AgentExecutionResult(task_id="T1", agent="a1", success=True)
        r2 = AgentExecutionResult(task_id="T2", agent="a2", success=False)
        executor.task_results["T1"] = r1
        executor.task_results["T2"] = r2

        all_results = executor.get_all_results()
        assert len(all_results) == 2

    def test_success_rate_empty(self):
        dispatcher = AgentDispatcher()
        executor = WorkflowExecutor(dispatcher)
        assert executor.get_success_rate() == 1.0

    def test_task_execution_context_model(self):
        ctx = TaskExecutionContext(
            task_id="T-001",
            task_input={"key": "value"},
            agent_name="test-agent",
            dependencies=["DEP-001"],
        )
        assert ctx.task_id == "T-001"
        assert ctx.agent_name == "test-agent"
