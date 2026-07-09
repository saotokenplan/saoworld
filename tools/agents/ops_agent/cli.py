import argparse
import json
from .ops_agent import OpsAgent
from .ops_input_schemas import (
    OpsTask, MetricsData, ExceptionData, FeedbackData, SystemMetrics, GameplayMetrics, ServiceMetrics,
    ExceptionItem, FeedbackItem
)
from datetime import datetime, timezone


def _create_sample_metrics() -> MetricsData:
    services = {}
    for svc in ["vote", "world", "content", "generation", "review", "player", "ops", "gateway"]:
        services[svc] = ServiceMetrics(
            http_requests_total=100000,
            http_errors_total=50,
            http_request_duration_p95=0.3,
            http_request_duration_p99=0.5,
            business_metrics={}
        )
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
            service="vote-service",
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


def main():
    parser = argparse.ArgumentParser(description="Ops Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    collect_metrics_parser = subparsers.add_parser("collect-metrics", help="采集监控数据")
    collect_metrics_parser.add_argument("--task-id", default="OPS-001", help="任务ID")
    collect_metrics_parser.add_argument("--period", default="24h", help="分析周期")
    collect_metrics_parser.add_argument("--service", action="append", default=None, help="目标服务")

    analyze_exc_parser = subparsers.add_parser("analyze-exceptions", help="分析异常模式")
    analyze_exc_parser.add_argument("--task-id", default="OPS-001", help="任务ID")

    gen_report_parser = subparsers.add_parser("generate-report", help="生成异常报告")
    gen_report_parser.add_argument("--task-id", default="OPS-001", help="任务ID")
    gen_report_parser.add_argument("--period", default="24h", help="统计周期")

    workflow_parser = subparsers.add_parser("run-workflow", help="运行完整运维工作流")
    workflow_parser.add_argument("--task-id", required=True, help="运维任务ID")
    workflow_parser.add_argument("--period", default="24h", help="分析周期")
    workflow_parser.add_argument("--type", default="full_workflow", help="任务类型")
    workflow_parser.add_argument("--title", default="自动运维分析", help="任务标题")

    args = parser.parse_args()
    agent = OpsAgent()

    if args.command == "collect-metrics":
        ops_task = OpsTask(
            ops_task_id=args.task_id,
            task_id="TASK-001",
            title="指标采集",
            type="health_check",
            period=args.period,
            target_services=args.service or [],
        )
        result = agent.collect_metrics(ops_task)
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "analyze-exceptions":
        exception_data = _create_sample_exceptions()
        result = agent.analyze_exceptions(exception_data)
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "generate-report":
        ops_task = OpsTask(
            ops_task_id=args.task_id,
            task_id="TASK-001",
            title="异常报告生成",
            type="exception_analysis",
            period=args.period,
        )
        exception_data = _create_sample_exceptions()
        result = agent.generate_exception_report(ops_task, exception_data)
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "run-workflow":
        ops_task = OpsTask(
            ops_task_id=args.task_id,
            task_id="TASK-001",
            title=args.title,
            type=args.type,
            period=args.period,
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
        print(json.dumps(result.model_dump(), indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
