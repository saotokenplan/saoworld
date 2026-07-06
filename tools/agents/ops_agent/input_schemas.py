from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ServiceMetrics(BaseModel):
    http_requests_total: int = Field(description="HTTP请求总数")
    http_errors_total: int = Field(description="HTTP错误总数")
    http_request_duration_p95: float = Field(description="P95请求延迟（秒）")
    http_request_duration_p99: float = Field(description="P99请求延迟（秒）")
    business_metrics: Dict[str, float] = Field(default_factory=dict, description="业务指标")


class SystemMetrics(BaseModel):
    cpu_usage: float = Field(description="CPU使用率（百分比）")
    memory_usage: float = Field(description="内存使用率（百分比）")
    disk_usage: float = Field(description="磁盘使用率（百分比）")
    network_latency: float = Field(description="网络延迟（毫秒）")


class GameplayMetrics(BaseModel):
    daily_active_users: int = Field(description="日活跃用户")
    vote_participation_rate: float = Field(description="投票参与率")
    task_completion_rate: float = Field(description="任务完成率")
    new_content_stay_time: float = Field(description="新内容停留时间（分钟）")
    crash_rate: float = Field(description="崩溃率")


class MetricsData(BaseModel):
    services: Dict[str, ServiceMetrics] = Field(description="各服务指标")
    system: SystemMetrics = Field(description="系统指标")
    gameplay: GameplayMetrics = Field(description="玩法指标")
    timestamp: str = Field(description="采集时间戳")


class LogEntry(BaseModel):
    timestamp: str = Field(description="日志时间戳")
    level: str = Field(description="日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL")
    service: str = Field(description="服务名称")
    request_id: Optional[str] = Field(default=None, description="请求ID")
    error_code: Optional[str] = Field(default=None, description="错误码")
    message: str = Field(description="日志消息")
    stack_trace: Optional[str] = Field(default=None, description="堆栈跟踪")


class LogData(BaseModel):
    logs: List[LogEntry] = Field(default_factory=list, description="日志条目列表")


class ExceptionItem(BaseModel):
    exception_id: str = Field(description="异常ID")
    type: str = Field(description="异常类型：crash/performance/error/availability")
    service: str = Field(description="服务名称")
    endpoint: Optional[str] = Field(default=None, description="端点（性能问题适用）")
    platform: Optional[str] = Field(default=None, description="平台（客户端问题适用）")
    count: int = Field(description="发生次数")
    impacted_users: int = Field(description="受影响用户数")
    stack_trace: Optional[str] = Field(default=None, description="堆栈跟踪")
    avg_response_time: Optional[float] = Field(default=None, description="平均响应时间（秒，性能问题适用）")
    threshold: Optional[float] = Field(default=None, description="阈值（秒，性能问题适用）")
    first_occurrence: str = Field(description="首次发生时间")
    last_occurrence: str = Field(description="最近发生时间")


class ExceptionData(BaseModel):
    exceptions: List[ExceptionItem] = Field(default_factory=list, description="异常列表")


class FeedbackItem(BaseModel):
    feedback_id: str = Field(description="反馈ID")
    player_id: str = Field(description="玩家ID")
    type: str = Field(description="反馈类型：bug/feature_request/suggestion/complaint")
    title: str = Field(description="反馈标题")
    description: str = Field(description="反馈描述")
    severity: str = Field(description="严重程度：low/medium/high/critical")
    status: str = Field(description="状态：open/pending/processing/resolved/closed")
    votes: int = Field(default=0, description="支持票数")
    created_at: str = Field(description="创建时间")


class FeedbackData(BaseModel):
    feedback_items: List[FeedbackItem] = Field(default_factory=list, description="反馈列表")


class OpsTask(BaseModel):
    ops_task_id: str = Field(description="运维任务ID")
    task_id: str = Field(description="关联任务ID")
    title: str = Field(description="任务标题")
    type: str = Field(description="任务类型：health_check/exception_analysis/report_generation/full_workflow")
    period: str = Field(default="24h", description="分析周期")
    target_services: List[str] = Field(default_factory=list, description="目标服务列表")
