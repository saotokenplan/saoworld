"""Workflow Executor: 负责按依赖关系顺序执行多代理工作流。

核心功能：
1. 拓扑排序：根据任务依赖关系确定执行顺序
2. 依赖传递：上游 Agent 的输出自动传递给下游 Agent
3. 并行执行：无依赖关系的任务可以并行执行
4. 失败处理：单个任务失败不影响其他独立任务的执行
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from .dispatcher import AgentDispatcher, AgentExecutionResult
from .orchestrator_input_schemas import TaskInput
from .orchestrator_output_schemas import (
    ExecutionEvent,
    ExecutionLog,
    FailureHandling,
    FailureError,
)

logger = logging.getLogger(__name__)


class TaskExecutionContext(BaseModel):
    """任务执行上下文"""
    task_id: str = ""
    task_input: Dict[str, Any] = {}
    agent_name: str = ""
    dependencies: List[str] = []


class WorkflowExecutor:
    """工作流执行器：按依赖关系调度和执行多 Agent 工作流"""

    def __init__(self, dispatcher: Optional[AgentDispatcher] = None) -> None:
        self.dispatcher = dispatcher or AgentDispatcher()
        self.task_results: Dict[str, AgentExecutionResult] = {}
        self.execution_logs: List[ExecutionLog] = []
        self.failures: List[FailureHandling] = []

    def topological_sort(self, tasks: List[TaskInput]) -> List[List[TaskInput]]:
        """对任务进行拓扑排序，返回可并行执行的批次

        Args:
            tasks: 任务列表

        Returns:
            按依赖关系排列的任务批次，每个批次内的任务可以并行执行

        Raises:
            ValueError: 存在循环依赖时抛出异常
        """
        # 构建邻接表和入度表
        task_map: Dict[str, TaskInput] = {t.id: t for t in tasks}
        in_degree: Dict[str, int] = {t.id: 0 for t in tasks}
        dependents: Dict[str, List[str]] = {t.id: [] for t in tasks}

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in in_degree:
                    in_degree[task.id] += 1
                    dependents.setdefault(dep_id, []).append(task.id)

        # Kahn's 算法进行拓扑排序
        batches: List[List[TaskInput]] = []
        remaining = set(in_degree.keys())

        while remaining:
            # 找到所有入度为 0 的节点（当前批次）
            current_batch = [task_map[tid] for tid in sorted(remaining) if in_degree.get(tid, 0) == 0]

            if not current_batch:
                # 剩余节点但无法找到入度为 0 的节点 → 循环依赖
                raise ValueError(f"检测到循环依赖，涉及任务: {', '.join(sorted(remaining))}")

            batches.append(current_batch)

            # 移除当前批次，更新入度
            for task in current_batch:
                remaining.discard(task.id)
                for dependent_id in dependents.get(task.id, []):
                    in_degree[dependent_id] -= 1

        return batches

    def _build_task_input(
        self,
        task: TaskInput,
        upstream_results: Dict[str, AgentExecutionResult],
    ) -> Dict[str, Any]:
        """构建任务的输入参数，包含上游输出

        Args:
            task: 当前任务
            upstream_results: 已完成任务的结果映射

        Returns:
            合并后的输入参数
        """
        base_input: Dict[str, Any] = {
            "task_id": task.id,
            "title": task.title,
            "type": task.type,
        }

        if task.params:
            base_input["params"] = task.params

        for dep_id in task.dependencies:
            if dep_id in upstream_results and upstream_results[dep_id].success:
                dep_output = upstream_results[dep_id].output
                base_input[f"input_from_{dep_id}"] = dep_output

        return base_input

    def execute_single_task(
        self,
        task: TaskInput,
        upstream_results: Dict[str, AgentExecutionResult],
    ) -> AgentExecutionResult:
        """执行单个任务

        Args:
            task: 要执行的任务
            upstream_results: 上游任务的结果

        Returns:
            执行结果
        """
        logger.info("executing_task: task=%s agent=%s", task.id, task.assignee)

        task_input = self._build_task_input(task, upstream_results)
        result = self.dispatch(
            agent_name=task.assignee,
            task_input=task_input,
            task_id=task.id,
        )

        return result

    def dispatch(self, **kwargs) -> AgentExecutionResult:
        """委托给 dispatcher 执行"""
        return self.dispatcher.dispatch(**kwargs)

    def execute_workflow(
        self,
        tasks: List[TaskInput],
        stop_on_failure: bool = False,
    ) -> tuple[List[ExecutionLog], List[FailureHandling]]:
        """执行完整工作流

        Args:
            tasks: 任务列表（含依赖关系）
            stop_on_failure: 是否在第一个失败时停止整个工作流

        Returns:
            (execution_logs, failures)
        """
        self.task_results.clear()
        self.execution_logs.clear()
        self.failures.clear()

        try:
            batches = self.topological_sort(tasks)
        except ValueError as e:
            failure = FailureHandling(
                failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
                task_id="WORKFLOW",
                agent="orchestrator",
                error=FailureError(
                    type="cyclic_dependency",
                    message=str(e),
                    details=str(e),
                ),
                retry_count=0,
                max_retries=0,
                retry_strategy="none",
                status="failed",
            )
            self.failures.append(failure)
            return self.execution_logs, self.failures

        for batch_idx, batch in enumerate(batches):
            logger.info(
                "executing_batch: %d/%d, tasks=%d",
                batch_idx + 1,
                len(batches),
                len(batch),
            )

            batch_failures: List[FailureHandling] = []

            for task in batch:
                start_time = datetime.now(timezone.utc)
                log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"

                events: List[ExecutionEvent] = [
                    ExecutionEvent(
                        timestamp=start_time.isoformat(),
                        event="task_started",
                        details=f"开始执行任务: {task.title}",
                    )
                ]

                result = self.execute_single_task(task, self.task_results)
                elapsed_sec = (datetime.now(timezone.utc) - start_time).total_seconds()
                duration_str = f"{elapsed_sec:.1f}s"

                if result.success:
                    events.append(
                        ExecutionEvent(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            event="task_completed",
                            details=f"任务 {task.title} 执行完成 ({result.duration_ms}ms)",
                        )
                    )
                    log = ExecutionLog(
                        log_id=log_id,
                        task_id=task.id,
                        agent=task.assignee,
                        events=events,
                        status="completed",
                        duration=duration_str,
                    )
                else:
                    events.append(
                        ExecutionEvent(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            event="task_failed",
                            details=f"任务 {task.title} 执行失败: {result.error}",
                        )
                    )
                    log = ExecutionLog(
                        log_id=log_id,
                        task_id=task.id,
                        agent=task.assignee,
                        events=events,
                        status="failed",
                        duration=duration_str,
                    )

                    failure = FailureHandling(
                        failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
                        task_id=task.id,
                        agent=task.assignee,
                        error=FailureError(
                            type="agent_failure",
                            message=f"任务 {task.title} 执行失败",
                            details=result.error or "未知错误",
                        ),
                        retry_count=0,
                        max_retries=3,
                        retry_strategy="exponential_backoff",
                        next_retry_time=(datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                        status="retrying",
                    )
                    batch_failures.append(failure)

                self.task_results[task.id] = result
                self.execution_logs.append(log)

                if result.success is False and stop_on_failure:
                    break

            self.failures.extend(batch_failures)

            if stop_on_failure and batch_failures:
                break

        return self.execution_logs, self.failures

    def get_task_result(self, task_id: str) -> Optional[AgentExecutionResult]:
        """获取指定任务的执行结果"""
        return self.task_results.get(task_id)

    def get_all_results(self) -> Dict[str, AgentExecutionResult]:
        """获取所有任务的执行结果"""
        return dict(self.task_results)

    def get_success_rate(self) -> float:
        """获取任务成功率"""
        total = len(self.task_results)
        if total == 0:
            return 1.0
        succeeded = sum(1 for r in self.task_results.values() if r.success)
        return succeeded / total
