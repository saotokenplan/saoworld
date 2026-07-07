import pytest
import sys
import os
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ops_agent import OpsAgent
from input_schemas import (
    OpsTask, MetricsData, ExceptionData, FeedbackData, LogData,
    ServiceMetrics, SystemMetrics, GameplayMetrics,
    ExceptionItem, FeedbackItem, LogEntry
)


def _create_sample_metrics() -> MetricsData:
    services = {}
    for svc in ["vote", "world", "content", "gateway"]:
        services[svc] = ServiceMetrics(
            http_requests_total=100000,
            http_errors_total=50,
            http_request_duration_p95=0.3,
            http_request_duration_p99=0.5,
            business_metrics={}
        )
    services["vote"].http_errors_total = 2000
    services["vote"].http_request_duration_p95 = 2.5
    return MetricsData(
        services=services,
        system=SystemMetrics(
            cpu_usage=60.0,
            memory_usage=75.0,
            disk_usage=45.0,
            network_latency=50.0
        ),
        gameplay=GameplayMetrics(
            daily_active_users=1200,
            vote_participation_rate=0.65,
            task_completion_rate=0.72,
            new_content_stay_time=45.0,
            crash_rate=0.015
        ),
        timestamp=datetime.now(timezone.utc).isoformat()
    )


def _create_sample_exceptions() -> ExceptionData:
    return ExceptionData(exceptions=[
        ExceptionItem(
            exception_id="EXC-001",
            type="performance",
            service="vote",
            endpoint="/api/v1/votes/submit",
            count=80,
            impacted_users=500,
            avg_response_time=2.5,
            threshold=1.0,
            first_occurrence="2026-07-07T00:00:00Z",
            last_occurrence="2026-07-07T23:59:59Z",
        ),
        ExceptionItem(
            exception_id="EXC-002",
            type="crash",
            service="client",
            platform="windows",
            count=15,
            impacted_users=12,
            stack_trace="memory access violation",
            first_occurrence="2026-07-07T10:00:00Z",
            last_occurrence="2026-07-07T22:00:00Z",
        ),
        ExceptionItem(
            exception_id="EXC-003",
            type="error",
            service="content",
            count=3,
            impacted_users=5,
            first_occurrence="2026-07-07T15:00:00Z",
            last_occurrence="2026-07-07T18:00:00Z",
        ),
    ])


def _create_sample_feedback() -> FeedbackData:
    return FeedbackData(feedback_items=[
        FeedbackItem(
            feedback_id="FB-001",
            player_id="player_xxx",
            type="bug",
            title="投票提交失败",
            description="点击提交按钮后没有反应",
            severity="high",
            status="open",
            votes=25,
            created_at="2026-07-07T21:30:00Z",
        ),
        FeedbackItem(
            feedback_id="FB-002",
            player_id="player_yyy",
            type="feature_request",
            title="希望增加地图标记功能",
            description="在世界地图上标记已探索区域",
            severity="medium",
            status="pending",
            votes=150,
            created_at="2026-07-07T20:00:00Z",
        ),
    ])


def test_collect_metrics():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="测试指标采集",
        type="health_check",
        period="24h",
        target_services=["vote", "world"],
    )
    result = agent.collect_metrics(ops_task)
    assert len(result.services) == 2
    assert "vote" in result.services
    assert "world" in result.services
    assert result.services["vote"].http_requests_total > 0
    assert result.system.cpu_usage > 0
    assert result.gameplay.daily_active_users > 0
    assert result.timestamp is not None


def test_collect_metrics_default_services():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="默认服务测试",
        type="health_check",
    )
    result = agent.collect_metrics(ops_task)
    assert len(result.services) == 8
    assert "vote" in result.services
    assert "gateway" in result.services


def test_analyze_exceptions():
    agent = OpsAgent()
    exception_data = _create_sample_exceptions()
    result = agent.analyze_exceptions(exception_data)
    assert len(result) == 3
    assert result[0]["severity_score"] >= result[1]["severity_score"]
    assert result[0]["priority"] in ("critical", "high", "medium", "low")
    assert result[0]["exception_id"] in ("EXC-001", "EXC-002", "EXC-003")


def test_analyze_exceptions_empty():
    agent = OpsAgent()
    exception_data = ExceptionData(exceptions=[])
    result = agent.analyze_exceptions(exception_data)
    assert len(result) == 0


def test_categorize_issues():
    agent = OpsAgent()
    exception_data = _create_sample_exceptions()
    analyzed = agent.analyze_exceptions(exception_data)
    metrics_data = _create_sample_metrics()
    feedback_data = _create_sample_feedback()
    result = agent.categorize_issues(analyzed, metrics_data, feedback_data)
    assert "by_service" in result
    assert "by_type" in result
    assert "high_priority_count" in result
    assert "total_exceptions" in result
    assert "feedback_summary" in result
    assert result["total_exceptions"] == 3
    assert "bug" in result["feedback_summary"]
    assert "feature_request" in result["feedback_summary"]


def test_generate_exception_report():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="异常报告测试",
        type="exception_analysis",
        period="24h",
    )
    exception_data = _create_sample_exceptions()
    report = agent.generate_exception_report(ops_task, exception_data)
    assert report.report_id.startswith("EXCEPTION-REPORT-")
    assert len(report.exceptions) == 3
    assert report.summary.total_exceptions == 3
    assert report.period == "24h"
    assert report.timestamp is not None
    for exc in report.exceptions:
        assert exc.exception_id is not None
        assert exc.type is not None
        assert exc.service is not None
        assert exc.description is not None
        assert exc.root_cause is not None
        assert exc.suggestion is not None
        assert exc.priority in ("critical", "high", "medium", "low")
        assert "count" in exc.impact
        assert "impacted_users" in exc.impact


def test_generate_exception_report_empty():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="空异常报告测试",
        type="exception_analysis",
        period="24h",
    )
    exception_data = ExceptionData(exceptions=[])
    report = agent.generate_exception_report(ops_task, exception_data)
    assert len(report.exceptions) == 0
    assert report.summary.total_exceptions == 0


def test_form_improvement_suggestions():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="改进建议测试",
        type="full_workflow",
    )
    exception_data = _create_sample_exceptions()
    metrics_data = _create_sample_metrics()
    feedback_data = _create_sample_feedback()
    exception_report = agent.generate_exception_report(ops_task, exception_data)
    suggestions = agent.form_improvement_suggestions(exception_report, metrics_data, feedback_data)
    assert len(suggestions.suggestions) > 0
    for sugg in suggestions.suggestions:
        assert sugg.suggestion_id.startswith("SUGG-")
        assert sugg.title is not None
        assert sugg.description is not None
        assert sugg.priority in ("P0", "P1", "P2", "P3")
        assert sugg.source in (
            "performance_monitor", "error_tracker", "player_feedback", "system_health"
        )
        assert sugg.target_agent in (
            "backend", "gameplay", "world", "product", "qa", "build"
        )


def test_generate_alert_summary():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="告警汇总测试",
        type="full_workflow",
        period="24h",
    )
    exception_data = _create_sample_exceptions()
    metrics_data = _create_sample_metrics()
    summary = agent.generate_alert_summary(ops_task, exception_data, metrics_data)
    assert summary.alert_summary.period == "24h"
    assert summary.alert_summary.timestamp is not None
    assert summary.alert_summary.alerts.total >= 0
    assert isinstance(summary.alert_summary.trends.increasing, list)
    assert isinstance(summary.alert_summary.top_alerts, list)
    if summary.alert_summary.top_alerts:
        assert summary.alert_summary.top_alerts[0].service is not None
        assert summary.alert_summary.top_alerts[0].type is not None
        assert summary.alert_summary.top_alerts[0].count >= 0


def test_generate_health_report():
    agent = OpsAgent()
    metrics_data = _create_sample_metrics()
    exception_data = _create_sample_exceptions()
    report = agent.generate_health_report(metrics_data, exception_data)
    assert report.health_report.timestamp is not None
    assert len(report.health_report.services) == 4
    assert report.health_report.overall_status in ("healthy", "degraded", "unhealthy")
    assert isinstance(report.health_report.issues, list)
    for svc_name, svc_health in report.health_report.services.items():
        assert svc_health.status in ("healthy", "degraded", "unhealthy")
        assert svc_health.error_rate >= 0
        assert svc_health.latency_p95 >= 0
        assert isinstance(svc_health.issues, list)


def test_generate_health_report_vote_degraded():
    agent = OpsAgent()
    metrics_data = _create_sample_metrics()
    exception_data = _create_sample_exceptions()
    report = agent.generate_health_report(metrics_data, exception_data)
    vote_health = report.health_report.services.get("vote")
    assert vote_health is not None
    assert vote_health.status in ("degraded", "unhealthy")
    assert len(vote_health.issues) > 0


def test_execute_ops_workflow_full():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="完整工作流测试",
        type="full_workflow",
        period="24h",
    )
    metrics_data = _create_sample_metrics()
    exception_data = _create_sample_exceptions()
    feedback_data = _create_sample_feedback()
    result = agent.execute_ops_workflow(
        ops_task,
        metrics_data=metrics_data,
        exception_data=exception_data,
        feedback_data=feedback_data,
    )
    assert result.success is True
    assert result.exception_report is not None
    assert result.improvement_suggestions is not None
    assert result.alert_summary is not None
    assert result.health_report is not None
    assert "运维分析工作流执行完成" in result.message


def test_execute_ops_workflow_default_data():
    agent = OpsAgent()
    ops_task = OpsTask(
        ops_task_id="OPS-001",
        task_id="TASK-001",
        title="默认数据测试",
        type="full_workflow",
    )
    result = agent.execute_ops_workflow(ops_task)
    assert result.success is True
    assert result.exception_report is not None
    assert result.health_report is not None
    assert len(result.exception_report.exceptions) == 0


def test_error_handler_collection_failure():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("collection_failure", "Prometheus连接失败")


def test_error_handler_data_inconsistency():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("data_inconsistency", "不同数据源数据不一致")


def test_error_handler_alert_storm():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("alert_storm", "短时间内大量告警")


def test_error_handler_analysis_failure():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("analysis_failure", "异常分析失败")


def test_error_handler_report_failure():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("report_failure", "报告生成失败")


def test_error_handler_workflow_error():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("workflow", "工作流执行异常")


def test_error_handler_generic_error():
    from tools.agents.ops_agent.error_handler import OpsErrorHandler
    handler = OpsErrorHandler()
    handler.handle_error("unknown_type", "未知错误类型")
