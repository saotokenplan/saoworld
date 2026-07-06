import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

from .input_schemas import VersionBrief, GateResults, AgentStatus, TaskInput
from .output_schemas import (
    TaskAssignment,
    ExecutionLog,
    ExecutionEvent,
    FailureHandling,
    FailureError,
    ProgressReport,
    MilestoneProgress,
    OrchestratorResult,
)
from .error_handler import OrchestratorErrorHandler


class Orchestrator:
    def __init__(self):
        self.version_brief: Optional[VersionBrief] = None
        self.gate_results: Optional[GateResults] = None
        self.agent_status: Optional[AgentStatus] = None
        self.task_definitions: List[TaskInput] = []
        self.assignments: List[TaskAssignment] = []
        self.execution_logs: List[ExecutionLog] = []
        self.failures: List[FailureHandling] = []
        self.error_handler = OrchestratorErrorHandler()

    def receive_version_brief(self, brief: VersionBrief) -> None:
        self.version_brief = brief
        self.task_definitions = brief.tasks.copy()

    def analyze_task_dependencies(self) -> Dict[str, List[str]]:
        dependency_map: Dict[str, List[str]] = {}
        for task in self.task_definitions:
            dependency_map[task.id] = task.dependencies.copy()
        return dependency_map

    def detect_cyclic_dependency(self, dependency_map: Dict[str, List[str]]) -> bool:
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            if node not in visited:
                visited.add(node)
                rec_stack.add(node)
                for neighbor in dependency_map.get(node, []):
                    if neighbor not in visited and has_cycle(neighbor):
                        return True
                    elif neighbor in rec_stack:
                        return True
            if node in rec_stack:
                rec_stack.remove(node)
            return False

        for node in dependency_map:
            if has_cycle(node):
                return True
        return False

    def assign_tasks(self) -> List[TaskAssignment]:
        assignments: List[TaskAssignment] = []
        now = datetime.now(timezone.utc)

        for task in self.task_definitions:
            if task.status != "pending":
                continue

            agent = task.assignee
            agent_status_item = self.agent_status.agent_status.get(agent) if self.agent_status else None
            if agent_status_item and agent_status_item.status != "idle":
                failure = self.error_handler.handle_task_assignment_failure(task.id, agent)
                self.failures.append(failure)
                continue

            deadline = (now + timedelta(days=7)).isoformat()
            assigned_at = now.isoformat()

            assignment = TaskAssignment(
                assignment_id=f"ASSIGN-{uuid.uuid4().hex[:8].upper()}",
                task_id=task.id,
                agent=agent,
                inputs={i: f"{i}/latest" for i in task.inputs},
                deadline=deadline,
                priority=task.priority,
                status="assigned",
                assigned_at=assigned_at,
            )
            assignments.append(assignment)
            task.status = "assigned"

        self.assignments.extend(assignments)
        return assignments

    def execute_tasks(self) -> List[ExecutionLog]:
        logs: List[ExecutionLog] = []
        now = datetime.now(timezone.utc)

        for assignment in self.assignments:
            if assignment.status != "assigned":
                continue

            log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
            start_time = now

            events = [
                ExecutionEvent(
                    timestamp=start_time.isoformat(),
                    event="task_started",
                    details=f"开始执行任务: {assignment.task_id}",
                )
            ]

            events.append(
                ExecutionEvent(
                    timestamp=(now + timedelta(hours=1)).isoformat(),
                    event="progress",
                    details="任务执行中...",
                )
            )

            events.append(
                ExecutionEvent(
                    timestamp=(now + timedelta(hours=2)).isoformat(),
                    event="task_completed",
                    details="任务执行完成",
                )
            )

            duration = "2h"
            status = "completed"

            log = ExecutionLog(
                log_id=log_id,
                task_id=assignment.task_id,
                agent=assignment.agent,
                events=events,
                status=status,
                duration=duration,
            )
            logs.append(log)
            assignment.status = "completed"

            for task in self.task_definitions:
                if task.id == assignment.task_id:
                    task.status = "completed"
                    break

        self.execution_logs.extend(logs)
        return logs

    def check_gates(self) -> bool:
        if not self.gate_results:
            return True

        all_passed = True
        for service, gates in self.gate_results.gate_results.items():
            if gates.lint.status != "pass" or gates.typecheck.status != "pass" or gates.tests.status != "pass":
                all_passed = False
                failure = self.error_handler.handle_gate_failure(service)
                self.failures.append(failure)

        return all_passed

    def handle_failures(self) -> List[FailureHandling]:
        handled_failures: List[FailureHandling] = []

        for failure in self.failures:
            if failure.status == "retrying" and failure.retry_count < failure.max_retries:
                failure.retry_count += 1
                next_retry = (datetime.now(timezone.utc) + timedelta(hours=2 ** failure.retry_count)).isoformat()
                failure.next_retry_time = next_retry
                handled_failures.append(failure)
            elif failure.retry_count >= failure.max_retries:
                failure.status = "failed"
                handled_failures.append(failure)

        return handled_failures

    def update_progress(self) -> ProgressReport:
        total = len(self.task_definitions)
        completed = sum(1 for t in self.task_definitions if t.status == "completed")
        in_progress = sum(1 for t in self.task_definitions if t.status in ("assigned", "in_progress"))
        pending = sum(1 for t in self.task_definitions if t.status == "pending")
        failed = sum(1 for t in self.task_definitions if t.status == "failed")

        overall_progress = int((completed / total) * 100) if total > 0 else 0

        milestones = []
        if self.version_brief:
            for m in self.version_brief.milestones:
                progress = 0
                status = "pending"
                if completed == total:
                    progress = 100
                    status = "completed"
                elif in_progress > 0:
                    progress = 50
                    status = "in_progress"
                milestones.append(
                    MilestoneProgress(
                        id=m.id,
                        name=m.name,
                        status=status,
                        progress=progress,
                    )
                )

        risks = []
        if failed > 0:
            risks.append(f"{failed}个任务执行失败")
        if not self.check_gates():
            risks.append("门禁检查未通过")

        report = ProgressReport(
            report_id=f"PROGRESS-{uuid.uuid4().hex[:8].upper()}",
            version=self.version_brief.version if self.version_brief else "unknown",
            timestamp=datetime.now(timezone.utc).isoformat(),
            tasks={
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "pending": pending,
                "failed": failed,
            },
            milestones=milestones,
            overall_progress=overall_progress,
            risks=risks,
        )

        return report

    def complete_phase(self) -> OrchestratorResult:
        progress_report = self.update_progress()
        success = progress_report.tasks["failed"] == 0 and self.check_gates()

        return OrchestratorResult(
            success=success,
            assignments=self.assignments,
            execution_logs=self.execution_logs,
            failures=self.failures,
            progress_report=progress_report,
            message="阶段执行完成" if success else "阶段执行存在问题",
        )

    def execute_workflow(
        self,
        brief: VersionBrief,
        gate_results: Optional[GateResults] = None,
        agent_status: Optional[AgentStatus] = None,
    ) -> OrchestratorResult:
        self.gate_results = gate_results
        self.agent_status = agent_status

        self.receive_version_brief(brief)

        dependency_map = self.analyze_task_dependencies()
        if self.detect_cyclic_dependency(dependency_map):
            failure = self.error_handler.handle_cyclic_dependency(list(dependency_map.keys()))
            self.failures.append(failure)
            return OrchestratorResult(
                success=False,
                assignments=[],
                execution_logs=[],
                failures=self.failures,
                progress_report=None,
                message="检测到循环依赖，无法执行工作流",
            )

        self.assign_tasks()
        self.execute_tasks()

        if not self.check_gates():
            self.handle_failures()

        return self.complete_phase()