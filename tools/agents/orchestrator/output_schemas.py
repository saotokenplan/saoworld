from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class TaskAssignment(BaseModel):
    assignment_id: str = Field(description="分配ID")
    task_id: str = Field(description="任务ID")
    agent: str = Field(description="指派代理")
    inputs: Dict[str, str] = Field(default_factory=dict, description="输入文件映射")
    deadline: str = Field(description="截止时间")
    priority: str = Field(description="优先级")
    status: str = Field(default="assigned", description="分配状态：assigned/in_progress/completed/failed")
    assigned_at: str = Field(description="分配时间")


class ExecutionEvent(BaseModel):
    timestamp: str = Field(description="事件时间戳")
    event: str = Field(description="事件类型：task_started/progress/task_completed/task_failed")
    details: str = Field(description="事件详情")


class ExecutionLog(BaseModel):
    log_id: str = Field(description="日志ID")
    task_id: str = Field(description="任务ID")
    agent: str = Field(description="执行代理")
    events: List[ExecutionEvent] = Field(default_factory=list, description="事件列表")
    status: str = Field(description="执行状态：completed/failed/in_progress")
    duration: str = Field(description="执行时长")


class FailureError(BaseModel):
    type: str = Field(description="错误类型：test_failure/gate_failure/timeout/no_response")
    message: str = Field(description="错误消息")
    details: str = Field(description="错误详情")


class FailureHandling(BaseModel):
    failure_id: str = Field(description="失败ID")
    task_id: str = Field(description="任务ID")
    agent: str = Field(description="执行代理")
    error: FailureError = Field(description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_strategy: str = Field(default="exponential_backoff", description="重试策略")
    next_retry_time: Optional[str] = Field(default=None, description="下次重试时间")
    status: str = Field(default="retrying", description="处理状态：retrying/failed/resolved")


class MilestoneProgress(BaseModel):
    id: str = Field(description="里程碑ID")
    name: str = Field(description="里程碑名称")
    status: str = Field(description="状态：completed/in_progress/pending")
    progress: int = Field(description="进度百分比")


class ProgressReport(BaseModel):
    report_id: str = Field(description="报告ID")
    version: str = Field(description="版本号")
    timestamp: str = Field(description="生成时间戳")
    tasks: Dict[str, int] = Field(description="任务统计：total/completed/in_progress/pending/failed")
    milestones: List[MilestoneProgress] = Field(description="里程碑进度")
    overall_progress: int = Field(description="整体进度百分比")
    risks: List[str] = Field(default_factory=list, description="风险列表")


class OrchestratorResult(BaseModel):
    success: bool = Field(description="是否成功")
    assignments: List[TaskAssignment] = Field(default_factory=list, description="任务分配列表")
    execution_logs: List[ExecutionLog] = Field(default_factory=list, description="执行日志列表")
    failures: List[FailureHandling] = Field(default_factory=list, description="失败处理列表")
    progress_report: Optional[ProgressReport] = Field(default=None, description="进度报告")
    message: str = Field(description="结果消息")