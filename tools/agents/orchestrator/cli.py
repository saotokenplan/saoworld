import argparse
import json
from datetime import datetime, timezone

from .orchestrator import Orchestrator
from .orchestrator_input_schemas import VersionBrief, GateResults, AgentStatus, Milestone, TaskInput, GateResult, ServiceGateResults, AgentStatusItem


def _create_sample_version_brief() -> VersionBrief:
    milestones = [
        Milestone(id="M1", name="设计完成", due_date="2026-07-10"),
        Milestone(id="M2", name="开发完成", due_date="2026-07-18"),
        Milestone(id="M3", name="测试完成", due_date="2026-07-22"),
        Milestone(id="M4", name="发布", due_date="2026-07-25"),
    ]
    tasks = [
        TaskInput(
            id="TASK-001",
            title="设计迷雾森林区域",
            priority="P1",
            assignee="system-designer-agent",
            type="design",
            inputs=["version_brief.md"],
            outputs=["design-note.md"],
            dependencies=[],
            status="pending",
        ),
        TaskInput(
            id="TASK-002",
            title="实现区域创建接口",
            priority="P1",
            assignee="backend-agent",
            type="implementation",
            inputs=["design-note.md"],
            outputs=["routes.py", "models.py", "tests.py"],
            dependencies=["TASK-001"],
            status="pending",
        ),
        TaskInput(
            id="TASK-003",
            title="创建区域场景",
            priority="P1",
            assignee="gameplay-agent",
            type="implementation",
            inputs=["design-note.md"],
            outputs=["scene.tscn", "script.gd"],
            dependencies=["TASK-001"],
            status="pending",
        ),
    ]
    return VersionBrief(
        version_brief_id="VB-001",
        version="0.2.0",
        objectives=["新增迷雾森林区域", "优化投票提交性能"],
        milestones=milestones,
        tasks=tasks,
    )


def _create_sample_gate_results() -> GateResults:
    gate_pass = GateResult(status="pass", timestamp=datetime.now(timezone.utc).isoformat())
    return GateResults(
        gate_results={
            "world-service": ServiceGateResults(lint=gate_pass, typecheck=gate_pass, tests=gate_pass),
            "game": ServiceGateResults(lint=gate_pass, typecheck=gate_pass, tests=gate_pass),
        }
    )


def _create_sample_agent_status() -> AgentStatus:
    return AgentStatus(
        agent_status={
            "product-agent": AgentStatusItem(status="idle", current_task=None),
            "system-designer-agent": AgentStatusItem(status="idle", current_task=None),
            "gameplay-agent": AgentStatusItem(status="idle", current_task=None),
            "world-agent": AgentStatusItem(status="idle", current_task=None),
            "backend-agent": AgentStatusItem(status="idle", current_task=None),
            "qa-agent": AgentStatusItem(status="idle", current_task=None),
            "build-agent": AgentStatusItem(status="idle", current_task=None),
            "ops-agent": AgentStatusItem(status="running", current_task="health_check"),
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    assign_parser = subparsers.add_parser("assign-task", help="分配任务")
    assign_parser.add_argument("--brief-id", default="VB-001", help="版本简报ID")

    workflow_parser = subparsers.add_parser("execute-workflow", help="执行完整工作流")
    workflow_parser.add_argument("--brief-id", required=True, help="版本简报ID")

    gates_parser = subparsers.add_parser("check-gates", help="检查门禁状态")

    report_parser = subparsers.add_parser("generate-report", help="生成进度报告")
    report_parser.add_argument("--brief-id", default="VB-001", help="版本简报ID")

    args = parser.parse_args()
    orchestrator = Orchestrator()

    if args.command == "assign-task":
        brief = _create_sample_version_brief()
        agent_status = _create_sample_agent_status()
        orchestrator.receive_version_brief(brief)
        orchestrator.agent_status = agent_status
        assignments = orchestrator.assign_tasks()
        print(json.dumps([a.model_dump() for a in assignments], indent=2))

    elif args.command == "execute-workflow":
        brief = _create_sample_version_brief()
        gate_results = _create_sample_gate_results()
        agent_status = _create_sample_agent_status()
        result = orchestrator.execute_workflow(brief, gate_results, agent_status)
        print(json.dumps(result.model_dump(), indent=2, default=str))

    elif args.command == "check-gates":
        gate_results = _create_sample_gate_results()
        orchestrator.gate_results = gate_results
        passed = orchestrator.check_gates()
        print(f"门禁检查结果: {'通过' if passed else '未通过'}")

    elif args.command == "generate-report":
        brief = _create_sample_version_brief()
        orchestrator.receive_version_brief(brief)
        report = orchestrator.update_progress()
        print(json.dumps(report.model_dump(), indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()