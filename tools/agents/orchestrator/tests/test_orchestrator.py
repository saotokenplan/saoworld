import pytest
from datetime import datetime, timezone

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
from ..orchestrator import Orchestrator


def _create_sample_brief(tasks=None):
    milestones = [
        Milestone(id="M1", name="设计完成", due_date="2026-07-10"),
        Milestone(id="M2", name="开发完成", due_date="2026-07-18"),
    ]
    if tasks is None:
        tasks = [
            TaskInput(
                id="TASK-001",
                title="设计区域",
                priority="P1",
                assignee="system-designer-agent",
                type="design",
                inputs=["brief.md"],
                outputs=["design.md"],
                dependencies=[],
                status="pending",
            ),
            TaskInput(
                id="TASK-002",
                title="实现接口",
                priority="P1",
                assignee="backend-agent",
                type="implementation",
                inputs=["design.md"],
                outputs=["routes.py"],
                dependencies=["TASK-001"],
                status="pending",
            ),
        ]
    return VersionBrief(
        version_brief_id="VB-001",
        version="0.2.0",
        objectives=["测试目标"],
        milestones=milestones,
        tasks=tasks,
    )


def _create_sample_gate_results(status="pass"):
    gate = GateResult(status=status, timestamp=datetime.now(timezone.utc).isoformat())
    return GateResults(
        gate_results={
            "world-service": ServiceGateResults(lint=gate, typecheck=gate, tests=gate),
        }
    )


def _create_sample_agent_status(agent_status_map=None):
    if agent_status_map is None:
        agent_status_map = {
            "system-designer-agent": ("idle", None),
            "backend-agent": ("idle", None),
        }
    agent_status = {}
    for agent, (status, task) in agent_status_map.items():
        agent_status[agent] = AgentStatusItem(status=status, current_task=task)
    return AgentStatus(agent_status=agent_status)


def test_receive_version_brief():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()

    orchestrator.receive_version_brief(brief)

    assert orchestrator.version_brief == brief
    assert len(orchestrator.task_definitions) == 2


def test_analyze_task_dependencies():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()

    orchestrator.receive_version_brief(brief)
    dependencies = orchestrator.analyze_task_dependencies()

    assert "TASK-001" in dependencies
    assert dependencies["TASK-001"] == []
    assert "TASK-002" in dependencies
    assert dependencies["TASK-002"] == ["TASK-001"]


def test_detect_cyclic_dependency_no_cycle():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()

    orchestrator.receive_version_brief(brief)
    dependencies = orchestrator.analyze_task_dependencies()

    assert not orchestrator.detect_cyclic_dependency(dependencies)


def test_detect_cyclic_dependency_with_cycle():
    orchestrator = Orchestrator()
    tasks = [
        TaskInput(id="TASK-A", title="任务A", priority="P1", assignee="agent1", type="design", dependencies=["TASK-B"]),
        TaskInput(id="TASK-B", title="任务B", priority="P1", assignee="agent2", type="design", dependencies=["TASK-A"]),
    ]
    brief = _create_sample_brief(tasks=tasks)

    orchestrator.receive_version_brief(brief)
    dependencies = orchestrator.analyze_task_dependencies()

    assert orchestrator.detect_cyclic_dependency(dependencies)


def test_assign_tasks_all_idle():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    agent_status = _create_sample_agent_status()

    orchestrator.receive_version_brief(brief)
    orchestrator.agent_status = agent_status

    assignments = orchestrator.assign_tasks()

    assert len(assignments) == 2
    assert assignments[0].task_id == "TASK-001"
    assert assignments[0].agent == "system-designer-agent"
    assert assignments[1].task_id == "TASK-002"
    assert assignments[1].agent == "backend-agent"


def test_assign_tasks_agent_busy():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    agent_status = _create_sample_agent_status({
        "system-designer-agent": ("busy", "OTHER-TASK"),
        "backend-agent": ("idle", None),
    })

    orchestrator.receive_version_brief(brief)
    orchestrator.agent_status = agent_status

    assignments = orchestrator.assign_tasks()

    assert len(assignments) == 1
    assert assignments[0].agent == "backend-agent"
    assert len(orchestrator.failures) == 1
    assert orchestrator.failures[0].task_id == "TASK-001"


def test_execute_tasks():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    agent_status = _create_sample_agent_status()

    orchestrator.receive_version_brief(brief)
    orchestrator.agent_status = agent_status
    orchestrator.assign_tasks()

    logs = orchestrator.execute_tasks()

    assert len(logs) == 2
    assert logs[0].status == "completed"
    assert logs[1].status == "completed"
    assert len(logs[0].events) == 3


def test_check_gates_pass():
    orchestrator = Orchestrator()
    gate_results = _create_sample_gate_results(status="pass")

    orchestrator.gate_results = gate_results
    passed = orchestrator.check_gates()

    assert passed


def test_check_gates_fail():
    orchestrator = Orchestrator()
    gate_results = _create_sample_gate_results(status="fail")

    orchestrator.gate_results = gate_results
    passed = orchestrator.check_gates()

    assert not passed
    assert len(orchestrator.failures) == 1


def test_update_progress():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()

    orchestrator.receive_version_brief(brief)

    report = orchestrator.update_progress()

    assert report.version == "0.2.0"
    assert report.tasks["total"] == 2
    assert report.tasks["completed"] == 0
    assert report.tasks["pending"] == 2
    assert report.overall_progress == 0


def test_update_progress_after_execution():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    agent_status = _create_sample_agent_status()

    orchestrator.receive_version_brief(brief)
    orchestrator.agent_status = agent_status
    orchestrator.assign_tasks()
    orchestrator.execute_tasks()

    report = orchestrator.update_progress()

    assert report.tasks["completed"] == 2
    assert report.overall_progress == 100


def test_complete_phase():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    agent_status = _create_sample_agent_status()
    gate_results = _create_sample_gate_results(status="pass")

    orchestrator.receive_version_brief(brief)
    orchestrator.agent_status = agent_status
    orchestrator.gate_results = gate_results
    orchestrator.assign_tasks()
    orchestrator.execute_tasks()

    result = orchestrator.complete_phase()

    assert result.success
    assert result.progress_report is not None
    assert result.progress_report.overall_progress == 100


def test_execute_workflow_success():
    orchestrator = Orchestrator()
    brief = _create_sample_brief()
    gate_results = _create_sample_gate_results(status="pass")
    agent_status = _create_sample_agent_status()

    result = orchestrator.execute_workflow(brief, gate_results, agent_status)

    assert result.success
    assert len(result.assignments) == 2
    assert len(result.execution_logs) == 2
    assert result.progress_report is not None


def test_execute_workflow_cyclic_dependency():
    orchestrator = Orchestrator()
    tasks = [
        TaskInput(id="TASK-A", title="任务A", priority="P1", assignee="agent1", type="design", dependencies=["TASK-B"]),
        TaskInput(id="TASK-B", title="任务B", priority="P1", assignee="agent2", type="design", dependencies=["TASK-A"]),
    ]
    brief = _create_sample_brief(tasks=tasks)

    result = orchestrator.execute_workflow(brief)

    assert not result.success
    assert "循环依赖" in result.message
    assert len(result.failures) == 1