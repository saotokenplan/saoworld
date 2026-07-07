"""多代理协同端到端集成测试

验证 Orchestrator 通过 AgentDispatcher 和 WorkflowExecutor
真实调度多个 Agent 完成完整工作流的能力。

使用 mock Agent 替代真实 Agent 实例，但走完整的调度链路：
Orchestrator → WorkflowExecutor → AgentDispatcher → Mock Agent
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from ..orchestrator import Orchestrator
from ..dispatcher import AgentDispatcher, AgentExecutionResult
from ..workflow_executor import WorkflowExecutor
from ..input_schemas import (
    VersionBrief,
    Milestone,
    TaskInput,
    GateResults,
    ServiceGateResults,
    GateResult,
    AgentStatus,
    AgentStatusItem,
)
from ..output_schemas import OrchestratorResult


def _create_mock_dispatcher() -> tuple[AgentDispatcher, dict]:
    """创建带有 mock Agent 的调度器

    Returns:
        (dispatcher, mock_agents) - 调度器和 mock Agent 字典
    """
    dispatcher = AgentDispatcher()

    # 创建所有 mock Agent
    mock_agents: dict[str, MagicMock] = {
        "product-agent": MagicMock(),
        "system-designer-agent": MagicMock(),
        "backend-agent": MagicMock(),
        "gameplay-agent": MagicMock(),
        "world-agent": MagicMock(),
        "qa-agent": MagicMock(),
        "build-agent": MagicMock(),
        "ops-agent": MagicMock(),
    }

    # 设置默认返回值
    mock_agents["product-agent"].run.return_value = {
        "version_brief_id": "VB-TEST",
        "version": "0.2.0",
        "objectives": ["新增迷雾森林区域"],
        "milestones": [],
        "tasks": [],
    }

    mock_agents["system-designer-agent"].execute_design_flow.return_value = {
        "design_note_id": "DN-001",
        "title": "迷雾森林区域设计",
        "architecture": "区域模块化架构",
        "data_structures": [],
        "api_interfaces": [],
        "changes": [],
    }

    mock_agents["backend-agent"].run_workflow.return_value = {
        "success": True,
        "service_name": "world-service",
        "models": ["Region"],
        "routes": ["/api/v1/world/regions/misty-forest"],
        "tests_passed": 12,
    }

    mock_agents["gameplay-agent"].execute_gameplay_flow.return_value = {
        "success": True,
        "scene_files": ["misty_forest.tscn"],
        "script_files": ["misty_forest.gd"],
        "tests_passed": 5,
    }

    mock_agents["world-agent"].execute_world_generation_flow.return_value = {
        "success": True,
        "npcs": [{"id": "npc_misty_01", "name": "迷雾守卫"}],
        "quests": [{"id": "quest_misty_01", "title": "迷雾中的秘密"}],
        "events": [],
    }

    mock_agents["qa-agent"].run_workflow.return_value = {
        "success": True,
        "total_tests": 25,
        "passed": 25,
        "failed": 0,
        "coverage": 0.92,
    }

    mock_agents["build-agent"].execute_build_workflow.return_value = {
        "success": True,
        "client_build": "ok",
        "server_build": "ok",
        "content_packages": 1,
    }

    mock_agents["ops-agent"].execute_ops_workflow.return_value = {
        "success": True,
        "health_report": {"status": "healthy"},
        "alerts": [],
    }

    # 注入 mock Agent 实例
    for name, mock in mock_agents.items():
        dispatcher._agent_instances[name] = mock

    return dispatcher, mock_agents


def _create_integration_brief() -> VersionBrief:
    """创建集成测试用版本简报"""
    return VersionBrief(
        version_brief_id="VB-INTEG-001",
        version="0.2.0",
        objectives=["新增迷雾森林区域", "灰度发布验证"],
        milestones=[
            Milestone(id="M1", name="设计完成", due_date="2026-07-15"),
            Milestone(id="M2", name="开发完成", due_date="2026-07-22"),
            Milestone(id="M3", name="测试完成", due_date="2026-07-25"),
            Milestone(id="M4", name="发布", due_date="2026-07-28"),
        ],
        tasks=[
            TaskInput(
                id="TASK-001",
                title="生成版本需求文档",
                priority="P0",
                assignee="product-agent",
                type="design",
                inputs=[],
                outputs=["version_brief.md"],
                dependencies=[],
            ),
            TaskInput(
                id="TASK-002",
                title="设计迷雾森林区域",
                priority="P1",
                assignee="system-designer-agent",
                type="design",
                inputs=["version_brief.md"],
                outputs=["design_note.md"],
                dependencies=["TASK-001"],
            ),
            TaskInput(
                id="TASK-003",
                title="实现区域创建接口",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                inputs=["design_note.md"],
                outputs=["routes.py", "models.py"],
                dependencies=["TASK-002"],
            ),
            TaskInput(
                id="TASK-004",
                title="创建区域场景",
                priority="P1",
                assignee="gameplay-agent",
                type="implementation",
                inputs=["design_note.md"],
                outputs=["scene.tscn", "script.gd"],
                dependencies=["TASK-002"],
            ),
            TaskInput(
                id="TASK-005",
                title="生成区域内容",
                priority="P1",
                assignee="world-agent",
                type="implementation",
                inputs=["design_note.md"],
                outputs=["npcs.json", "quests.json"],
                dependencies=["TASK-002"],
            ),
            TaskInput(
                id="TASK-006",
                title="运行测试验证",
                priority="P0",
                assignee="qa-agent",
                type="test",
                inputs=["routes.py", "scene.tscn"],
                outputs=["test_report.md"],
                dependencies=["TASK-003", "TASK-004", "TASK-005"],
            ),
            TaskInput(
                id="TASK-007",
                title="构建发布包",
                priority="P1",
                assignee="build-agent",
                type="build",
                inputs=["test_report.md"],
                outputs=["build_report.md"],
                dependencies=["TASK-006"],
            ),
            TaskInput(
                id="TASK-008",
                title="运行运维检查",
                priority="P2",
                assignee="ops-agent",
                type="ops",
                inputs=[],
                outputs=["ops_report.md"],
                dependencies=[],
            ),
        ],
    )


def _create_pass_gate_results() -> GateResults:
    gate = GateResult(status="pass", timestamp=datetime.now(timezone.utc).isoformat())
    return GateResults(
        gate_results={
            "world-service": ServiceGateResults(lint=gate, typecheck=gate, tests=gate),
            "game": ServiceGateResults(lint=gate, typecheck=gate, tests=gate),
        }
    )


def _create_all_idle_status() -> AgentStatus:
    agents = [
        "product-agent",
        "system-designer-agent",
        "backend-agent",
        "gameplay-agent",
        "world-agent",
        "qa-agent",
        "build-agent",
        "ops-agent",
    ]
    return AgentStatus(
        agent_status={a: AgentStatusItem(status="idle", current_task=None) for a in agents}
    )


class TestMultiAgentIntegration:
    """多代理协同端到端集成测试"""

    def test_full_workflow_product_to_build(self):
        """测试完整链路：Product Agent → System Designer → Backend/Gameplay/World → QA → Build"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        orchestrator = Orchestrator(dispatcher=dispatcher, use_real_dispatch=True)

        brief = _create_integration_brief()
        gate_results = _create_pass_gate_results()
        agent_status = _create_all_idle_status()

        result = orchestrator.execute_workflow(brief, gate_results, agent_status)

        # 验证整体结果
        assert result.success
        assert len(result.assignments) == 8
        assert len(result.execution_logs) == 8
        assert result.progress_report is not None
        assert result.progress_report.tasks["completed"] == 8
        assert result.progress_report.tasks["failed"] == 0
        assert result.progress_report.overall_progress == 100

    def test_agent_dispatch_order_respects_dependencies(self):
        """验证 Agent 调度顺序遵循依赖关系"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        brief = _create_integration_brief()
        logs, failures = executor.execute_workflow(brief.tasks)

        # 所有任务应该成功
        assert len(failures) == 0

        # 验证依赖关系：product-agent 应该最先被调用
        product_call_order = None
        designer_call_order = None
        backend_call_order = None
        qa_call_order = None

        for i, log in enumerate(logs):
            if log.task_id == "TASK-001":
                product_call_order = i
            elif log.task_id == "TASK-002":
                designer_call_order = i
            elif log.task_id == "TASK-003":
                backend_call_order = i
            elif log.task_id == "TASK-006":
                qa_call_order = i

        assert product_call_order is not None
        assert designer_call_order is not None
        assert backend_call_order is not None
        assert qa_call_order is not None

        # Product 应在 System Designer 之前
        assert product_call_order < designer_call_order
        # System Designer 应在 Backend 之前
        assert designer_call_order < backend_call_order
        # Backend 应在 QA 之前
        assert backend_call_order < qa_call_order

    def test_upstream_output_passed_to_downstream(self):
        """验证上游 Agent 输出被传递给下游 Agent"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        # 创建简单的链路
        tasks = [
            TaskInput(
                id="TASK-001",
                title="生成需求",
                priority="P1",
                assignee="product-agent",
                type="design",
                dependencies=[],
            ),
            TaskInput(
                id="TASK-002",
                title="设计方案",
                priority="P1",
                assignee="system-designer-agent",
                type="design",
                dependencies=["TASK-001"],
            ),
        ]

        logs, failures = executor.execute_workflow(tasks)
        assert len(failures) == 0

        # 验证 system-designer-agent 收到了 product-agent 的输出
        designer_call = mock_agents["system-designer-agent"].execute_design_flow
        assert designer_call.called
        call_kwargs = designer_call.call_args.kwargs
        # 检查是否收到了上游输出
        assert "input_from_TASK-001" in call_kwargs

    def test_parallel_tasks_executed(self):
        """验证无依赖关系的任务在同一个批次中执行"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        # TASK-003, TASK-004, TASK-005 都依赖 TASK-002，彼此无依赖
        tasks = [
            TaskInput(
                id="TASK-001",
                title="设计",
                priority="P1",
                assignee="product-agent",
                type="design",
                dependencies=[],
            ),
            TaskInput(
                id="TASK-002",
                title="详细设计",
                priority="P1",
                assignee="system-designer-agent",
                type="design",
                dependencies=["TASK-001"],
            ),
            TaskInput(
                id="TASK-003",
                title="后端实现",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                dependencies=["TASK-002"],
            ),
            TaskInput(
                id="TASK-004",
                title="客户端实现",
                priority="P1",
                assignee="gameplay-agent",
                type="implementation",
                dependencies=["TASK-002"],
            ),
            TaskInput(
                id="TASK-005",
                title="内容生成",
                priority="P1",
                assignee="world-agent",
                type="implementation",
                dependencies=["TASK-002"],
            ),
        ]

        batches = executor.topological_sort(tasks)
        assert len(batches) == 3
        # 第二个批次应该包含 TASK-002
        assert len(batches[1]) == 1
        # 第三个批次应该包含 TASK-003, TASK-004, TASK-005
        assert len(batches[2]) == 3

    def test_workflow_with_partial_failure(self):
        """测试部分 Agent 执行失败时的工作流行为"""
        dispatcher, mock_agents = _create_mock_dispatcher()

        # 让 backend-agent 执行失败
        mock_agents["backend-agent"].run_workflow.side_effect = RuntimeError("数据库连接失败")

        executor = WorkflowExecutor(dispatcher)

        tasks = [
            TaskInput(
                id="TASK-001",
                title="设计",
                priority="P1",
                assignee="product-agent",
                type="design",
                dependencies=[],
            ),
            TaskInput(
                id="TASK-002",
                title="实现",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                dependencies=["TASK-001"],
            ),
            TaskInput(
                id="TASK-003",
                title="运维检查",
                priority="P2",
                assignee="ops-agent",
                type="ops",
                dependencies=[],
            ),
        ]

        logs, failures = executor.execute_workflow(tasks)

        # TASK-001 和 TASK-003 应该成功，TASK-002 应该失败
        assert len(failures) == 1
        assert failures[0].task_id == "TASK-002"
        assert executor.get_task_result("TASK-001").success
        assert not executor.get_task_result("TASK-002").success
        assert executor.get_task_result("TASK-003").success

    def test_orchestrator_real_dispatch_mode(self):
        """测试 Orchestrator 的真实调度模式"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        orchestrator = Orchestrator(dispatcher=dispatcher, use_real_dispatch=True)

        brief = VersionBrief(
            version_brief_id="VB-SMALL",
            version="0.2.0",
            objectives=["小规模测试"],
            milestones=[Milestone(id="M1", name="完成", due_date="2026-07-10")],
            tasks=[
                TaskInput(
                    id="T1",
                    title="生成需求",
                    priority="P1",
                    assignee="product-agent",
                    type="design",
                    dependencies=[],
                ),
                TaskInput(
                    id="T2",
                    title="设计方案",
                    priority="P1",
                    assignee="system-designer-agent",
                    type="design",
                    dependencies=["T1"],
                ),
            ],
        )

        gate_results = _create_pass_gate_results()
        agent_status = _create_all_idle_status()

        result = orchestrator.execute_workflow(brief, gate_results, agent_status)

        assert result.success
        assert len(result.execution_logs) == 2

        # 验证真实调度：mock agents 应该被调用
        assert mock_agents["product-agent"].run.called
        assert mock_agents["system-designer-agent"].execute_design_flow.called

    def test_orchestrator_simulated_mode_compatibility(self):
        """测试 Orchestrator 的模拟模式（向后兼容）"""
        orchestrator = Orchestrator(use_real_dispatch=False)

        brief = VersionBrief(
            version_brief_id="VB-SIM",
            version="0.2.0",
            objectives=["模拟测试"],
            milestones=[],
            tasks=[
                TaskInput(
                    id="T1",
                    title="设计",
                    priority="P1",
                    assignee="system-designer-agent",
                    type="design",
                    dependencies=[],
                ),
            ],
        )

        result = orchestrator.execute_workflow(brief)

        assert result.success
        assert len(result.execution_logs) == 1
        assert result.execution_logs[0].status == "completed"

    def test_product_to_backend_chain(self):
        """测试 Product → System Designer → Backend 链路"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        tasks = [
            TaskInput(
                id="T1",
                title="生成版本需求",
                priority="P0",
                assignee="product-agent",
                type="design",
                dependencies=[],
            ),
            TaskInput(
                id="T2",
                title="系统设计",
                priority="P1",
                assignee="system-designer-agent",
                type="design",
                dependencies=["T1"],
            ),
            TaskInput(
                id="T3",
                title="后端实现",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                dependencies=["T2"],
            ),
        ]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 3
        assert len(failures) == 0
        assert all(log.status == "completed" for log in logs)

        # 验证所有 mock 被正确调用
        assert mock_agents["product-agent"].run.called
        assert mock_agents["system-designer-agent"].execute_design_flow.called
        assert mock_agents["backend-agent"].run_workflow.called

    def test_qa_after_implementation(self):
        """测试 QA Agent 在实现完成后执行"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        tasks = [
            TaskInput(
                id="T1",
                title="后端实现",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                dependencies=[],
            ),
            TaskInput(
                id="T2",
                title="QA测试",
                priority="P0",
                assignee="qa-agent",
                type="test",
                dependencies=["T1"],
            ),
        ]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 2
        assert len(failures) == 0
        # QA 应在 Backend 之后执行
        backend_idx = next(i for i, l in enumerate(logs) if l.task_id == "T1")
        qa_idx = next(i for i, l in enumerate(logs) if l.task_id == "T2")
        assert backend_idx < qa_idx

    def test_ops_agent_independent(self):
        """测试 Ops Agent 可以独立于其他 Agent 执行"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        executor = WorkflowExecutor(dispatcher)

        tasks = [
            TaskInput(
                id="T1",
                title="开发任务",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                dependencies=[],
            ),
            TaskInput(
                id="T2",
                title="运维检查",
                priority="P2",
                assignee="ops-agent",
                type="ops",
                dependencies=[],
            ),
        ]

        logs, failures = executor.execute_workflow(tasks)

        assert len(logs) == 2
        assert len(failures) == 0
        # 两个任务应该在同一个批次中（并行执行）
        batches = executor.topological_sort(tasks)
        assert len(batches) == 1
        assert len(batches[0]) == 2

    def test_full_eight_agent_pipeline(self):
        """测试全部 8 个 Agent 的完整流水线"""
        dispatcher, mock_agents = _create_mock_dispatcher()
        orchestrator = Orchestrator(dispatcher=dispatcher, use_real_dispatch=True)

        brief = _create_integration_brief()
        gate_results = _create_pass_gate_results()
        agent_status = _create_all_idle_status()

        result = orchestrator.execute_workflow(brief, gate_results, agent_status)

        assert result.success
        assert result.progress_report.tasks["completed"] == 8

        # 验证所有 Agent 都被调用
        assert mock_agents["product-agent"].run.called
        assert mock_agents["system-designer-agent"].execute_design_flow.called
        assert mock_agents["backend-agent"].run_workflow.called
        assert mock_agents["gameplay-agent"].execute_gameplay_flow.called
        assert mock_agents["world-agent"].execute_world_generation_flow.called
        assert mock_agents["qa-agent"].run_workflow.called
        assert mock_agents["build-agent"].execute_build_workflow.called
        assert mock_agents["ops-agent"].execute_ops_workflow.called
