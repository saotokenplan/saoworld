import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from .orchestrator_output_schemas import FailureHandling, FailureError


class OrchestratorErrorHandler:
    def handle_task_assignment_failure(self, task_id: str, agent: str) -> FailureHandling:
        return FailureHandling(
            failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            agent=agent,
            error=FailureError(
                type="assignment_failure",
                message="无法分配任务给代理",
                details=f"代理 {agent} 当前状态非空闲",
            ),
            retry_count=0,
            max_retries=3,
            retry_strategy="exponential_backoff",
            next_retry_time=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            status="retrying",
        )

    def handle_agent_no_response(self, task_id: str, agent: str) -> FailureHandling:
        return FailureHandling(
            failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            agent=agent,
            error=FailureError(
                type="no_response",
                message="代理无响应",
                details=f"代理 {agent} 在超时时间内未响应任务 {task_id}",
            ),
            retry_count=0,
            max_retries=3,
            retry_strategy="exponential_backoff",
            next_retry_time=(datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            status="retrying",
        )

    def handle_gate_failure(self, service: str) -> FailureHandling:
        return FailureHandling(
            failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
            task_id="GATE_CHECK",
            agent="orchestrator",
            error=FailureError(
                type="gate_failure",
                message="门禁检查失败",
                details=f"服务 {service} 的门禁检查未通过",
            ),
            retry_count=0,
            max_retries=2,
            retry_strategy="exponential_backoff",
            next_retry_time=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            status="retrying",
        )

    def handle_task_timeout(self, task_id: str, agent: str) -> FailureHandling:
        return FailureHandling(
            failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            agent=agent,
            error=FailureError(
                type="timeout",
                message="任务执行超时",
                details=f"任务 {task_id} 执行时间超过截止时间",
            ),
            retry_count=0,
            max_retries=2,
            retry_strategy="exponential_backoff",
            next_retry_time=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
            status="retrying",
        )

    def handle_cyclic_dependency(self, task_ids: List[str]) -> FailureHandling:
        return FailureHandling(
            failure_id=f"FAIL-{uuid.uuid4().hex[:8].upper()}",
            task_id="CYCLE_DETECTED",
            agent="orchestrator",
            error=FailureError(
                type="cyclic_dependency",
                message="检测到循环依赖",
                details=f"任务之间存在循环依赖: {', '.join(task_ids)}",
            ),
            retry_count=0,
            max_retries=0,
            retry_strategy="none",
            status="failed",
        )