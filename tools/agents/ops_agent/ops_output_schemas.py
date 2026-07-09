from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ExceptionDetail(BaseModel):
    exception_id: str = Field(description="异常ID")
    type: str = Field(description="异常类型")
    service: str = Field(description="服务名称")
    description: str = Field(description="问题描述")
    impact: Dict[str, float] = Field(description="影响范围（用户数、次数等）")
    root_cause: str = Field(description="根因分析")
    suggestion: str = Field(description="改进建议")
    priority: str = Field(description="优先级：low/medium/high/critical")


class ExceptionSummary(BaseModel):
    total_exceptions: int = Field(description="异常总数")
    critical_priority: int = Field(description="紧急优先级数量")
    high_priority: int = Field(description="高优先级数量")
    medium_priority: int = Field(description="中优先级数量")
    low_priority: int = Field(description="低优先级数量")


class ExceptionReport(BaseModel):
    report_id: str = Field(description="报告ID")
    timestamp: str = Field(description="生成时间戳")
    period: str = Field(description="统计周期")
    exceptions: List[ExceptionDetail] = Field(default_factory=list, description="异常详情列表")
    summary: ExceptionSummary = Field(description="异常摘要")


class ImprovementSuggestion(BaseModel):
    suggestion_id: str = Field(description="建议ID")
    title: str = Field(description="建议标题")
    description: str = Field(description="建议描述")
    priority: str = Field(description="优先级：P0/P1/P2/P3")
    source: str = Field(description="来源：performance_monitor/error_tracker/player_feedback/system_health")
    data_support: Dict[str, float] = Field(default_factory=dict, description="数据支持")
    target_agent: str = Field(description="目标代理：backend/gameplay/world/product/qa/build")


class ImprovementSuggestions(BaseModel):
    suggestions: List[ImprovementSuggestion] = Field(default_factory=list, description="改进建议列表")


class AlertCounts(BaseModel):
    total: int = Field(description="告警总数")
    critical: int = Field(description="紧急告警数")
    high: int = Field(description="高级告警数")
    medium: int = Field(description="中级告警数")
    low: int = Field(description="低级告警数")


class AlertTrends(BaseModel):
    increasing: List[str] = Field(default_factory=list, description="上升趋势告警")
    decreasing: List[str] = Field(default_factory=list, description="下降趋势告警")
    stable: List[str] = Field(default_factory=list, description="稳定告警")


class TopAlert(BaseModel):
    service: str = Field(description="服务名称")
    type: str = Field(description="告警类型")
    count: int = Field(description="告警次数")


class AlertSummaryData(BaseModel):
    timestamp: str = Field(description="统计时间戳")
    period: str = Field(description="统计周期")
    alerts: AlertCounts = Field(description="告警数量统计")
    trends: AlertTrends = Field(description="告警趋势")
    top_alerts: List[TopAlert] = Field(default_factory=list, description="Top告警列表")


class AlertSummary(BaseModel):
    alert_summary: AlertSummaryData = Field(description="告警汇总数据")


class ServiceHealth(BaseModel):
    status: str = Field(description="健康状态：healthy/degraded/unhealthy")
    error_rate: float = Field(description="错误率（百分比）")
    latency_p95: float = Field(description="P95延迟（秒）")
    issues: List[str] = Field(default_factory=list, description="问题列表")


class HealthReportData(BaseModel):
    timestamp: str = Field(description="报告时间戳")
    services: Dict[str, ServiceHealth] = Field(description="各服务健康状态")
    overall_status: str = Field(description="整体健康状态：healthy/degraded/unhealthy")
    issues: List[str] = Field(default_factory=list, description="整体问题列表")


class HealthReport(BaseModel):
    health_report: HealthReportData = Field(description="健康报告数据")


class OpsResult(BaseModel):
    success: bool = Field(description="是否成功")
    exception_report: Optional[ExceptionReport] = Field(default=None, description="异常报告")
    improvement_suggestions: Optional[ImprovementSuggestions] = Field(default=None, description="改进建议")
    alert_summary: Optional[AlertSummary] = Field(default=None, description="告警汇总")
    health_report: Optional[HealthReport] = Field(default=None, description="服务健康报告")
    message: str = Field(description="结果消息")
