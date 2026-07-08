import uuid
import random
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from .input_schemas import (
    MetricsData, LogData, ExceptionData, FeedbackData, OpsTask,
    ServiceMetrics, SystemMetrics, GameplayMetrics
)
from .output_schemas import (
    ExceptionReport, ExceptionDetail, ExceptionSummary,
    ImprovementSuggestion, ImprovementSuggestions,
    AlertSummary, AlertSummaryData, AlertCounts, AlertTrends, TopAlert,
    HealthReport, HealthReportData, ServiceHealth,
    OpsResult
)
from .error_handler import OpsErrorHandler


class OpsAgent:
    def __init__(self):
        self.error_handler = OpsErrorHandler()

    def collect_metrics(
        self,
        ops_task: OpsTask,
    ) -> MetricsData:
        services = {}
        target_services = ops_task.target_services or [
            "vote", "world", "content", "generation", "review", "player", "ops", "gateway"
        ]
        for svc in target_services:
            services[svc] = ServiceMetrics(
                http_requests_total=100000 + hash(svc) % 50000,
                http_errors_total=50 + hash(svc) % 100,
                http_request_duration_p95=0.2 + (hash(svc) % 100) / 500.0,
                http_request_duration_p99=0.4 + (hash(svc) % 100) / 300.0,
                business_metrics={}
            )
        system = SystemMetrics(
            cpu_usage=45.0,
            memory_usage=60.0,
            disk_usage=35.0,
            network_latency=20.0
        )
        gameplay = GameplayMetrics(
            daily_active_users=1200,
            vote_participation_rate=0.65,
            task_completion_rate=0.72,
            new_content_stay_time=45.0,
            crash_rate=0.015
        )
        return MetricsData(
            services=services,
            system=system,
            gameplay=gameplay,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def analyze_exceptions(
        self,
        exception_data: ExceptionData,
    ) -> List[Dict]:
        analyzed: List[Dict[str, Any]] = []
        for exc in exception_data.exceptions:
            freq_score = min(exc.count / 100.0, 1.0)
            impact_score = min(exc.impacted_users / 500.0, 1.0)
            severity = freq_score * 0.4 + impact_score * 0.6

            if severity > 0.7:
                priority = "critical"
            elif severity > 0.4:
                priority = "high"
            elif severity > 0.2:
                priority = "medium"
            else:
                priority = "low"

            trend = "increasing" if exc.count > 10 else "stable"

            analyzed.append({
                "exception_id": exc.exception_id,
                "type": exc.type,
                "service": exc.service,
                "severity_score": severity,
                "priority": priority,
                "trend": trend,
                "count": exc.count,
                "impacted_users": exc.impacted_users,
            })
        analyzed.sort(key=lambda x: x["severity_score"], reverse=True)
        return analyzed

    def categorize_issues(
        self,
        analyzed_exceptions: List[Dict],
        metrics_data: MetricsData,
        feedback_data: FeedbackData,
    ) -> Dict:
        by_service: Dict[str, List[Dict]] = {}
        by_type: Dict[str, List[Dict]] = {}

        for exc in analyzed_exceptions:
            svc = exc["service"]
            if svc not in by_service:
                by_service[svc] = []
            by_service[svc].append(exc)

            exc_type = exc["type"]
            if exc_type not in by_type:
                by_type[exc_type] = []
            by_type[exc_type].append(exc)

        high_priority_count = sum(
            1 for exc in analyzed_exceptions
            if exc["priority"] in ("critical", "high")
        )

        feedback_by_type: Dict[str, int] = {}
        for fb in feedback_data.feedback_items:
            fb_type = fb.type
            feedback_by_type[fb_type] = feedback_by_type.get(fb_type, 0) + 1

        return {
            "by_service": by_service,
            "by_type": by_type,
            "high_priority_count": high_priority_count,
            "total_exceptions": len(analyzed_exceptions),
            "feedback_summary": feedback_by_type,
        }

    def generate_exception_report(
        self,
        ops_task: OpsTask,
        exception_data: ExceptionData,
    ) -> ExceptionReport:
        analyzed = self.analyze_exceptions(exception_data)

        details = []
        for exc_info in analyzed:
            original = next(
                (e for e in exception_data.exceptions if e.exception_id == exc_info["exception_id"]),
                None
            )
            if not original:
                continue

            if original.type == "crash":
                root_cause = "内存访问异常或空指针引用"
                suggestion = "添加空值检查，优化内存管理"
                description = f"{original.service} 服务发生崩溃"
            elif original.type == "performance":
                root_cause = "数据库查询优化不足或缓存策略不当"
                suggestion = "添加索引，优化查询，增加缓存层"
                description = f"{original.service} 服务{original.endpoint} 接口响应慢"
            elif original.type == "error":
                root_cause = "业务逻辑异常或输入校验不足"
                suggestion = "完善错误处理，增加参数校验"
                description = f"{original.service} 服务错误率升高"
            else:
                root_cause = "待进一步分析"
                suggestion = "深入排查根因"
                description = f"{original.service} 服务异常"

            impact = {
                "count": float(original.count),
                "impacted_users": float(original.impacted_users),
            }
            if original.avg_response_time is not None:
                impact["avg_response_time"] = original.avg_response_time

            details.append(ExceptionDetail(
                exception_id=original.exception_id,
                type=original.type,
                service=original.service,
                description=description,
                impact=impact,
                root_cause=root_cause,
                suggestion=suggestion,
                priority=exc_info["priority"]
            ))

        critical = sum(1 for d in details if d.priority == "critical")
        high = sum(1 for d in details if d.priority == "high")
        medium = sum(1 for d in details if d.priority == "medium")
        low = sum(1 for d in details if d.priority == "low")

        summary = ExceptionSummary(
            total_exceptions=len(details),
            critical_priority=critical,
            high_priority=high,
            medium_priority=medium,
            low_priority=low,
        )

        return ExceptionReport(
            report_id=f"EXCEPTION-REPORT-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            period=ops_task.period,
            exceptions=details,
            summary=summary,
        )

    def form_improvement_suggestions(
        self,
        exception_report: ExceptionReport,
        metrics_data: MetricsData,
        feedback_data: FeedbackData,
    ) -> ImprovementSuggestions:
        suggestions: List[ImprovementSuggestion] = []
        sugg_id = 0

        for exc in exception_report.exceptions:
            sugg_id += 1
            if exc.type == "performance":
                target = "backend"
                source = "performance_monitor"
            elif exc.type == "crash":
                target = "backend" if exc.service != "client" else "gameplay"
                source = "error_tracker"
            else:
                target = "backend"
                source = "error_tracker"

            priority_map = {
                "critical": "P0",
                "high": "P1",
                "medium": "P2",
                "low": "P3",
            }

            suggestions.append(ImprovementSuggestion(
                suggestion_id=f"SUGG-{sugg_id:03d}",
                title=exc.description,
                description=exc.suggestion,
                priority=priority_map.get(exc.priority, "P2"),
                source=source,
                data_support=exc.impact,
                target_agent=target,
            ))

        for fb in feedback_data.feedback_items:
            sugg_id += 1
            if fb.severity == "critical":
                priority = "P0"
            elif fb.severity == "high":
                priority = "P1"
            elif fb.severity == "medium":
                priority = "P2"
            else:
                priority = "P3"

            target = "gameplay"
            if fb.type == "bug":
                source = "player_feedback"
            elif fb.type == "feature_request":
                source = "player_feedback"
                target = "product"
            else:
                source = "player_feedback"

            suggestions.append(ImprovementSuggestion(
                suggestion_id=f"SUGG-{sugg_id:03d}",
                title=fb.title,
                description=fb.description,
                priority=priority,
                source=source,
                data_support={"votes": float(fb.votes), "severity_score": 0.5},
                target_agent=target,
            ))

        error_rate_issues = []
        for svc_name, svc_metrics in metrics_data.services.items():
            if svc_metrics.http_requests_total > 0:
                error_rate = svc_metrics.http_errors_total / svc_metrics.http_requests_total
                if error_rate > 0.01:
                    sugg_id += 1
                    error_rate_issues.append(svc_name)
                    suggestions.append(ImprovementSuggestion(
                        suggestion_id=f"SUGG-{sugg_id:03d}",
                        title=f"{svc_name} 服务错误率过高",
                        description=f"{svc_name} 服务错误率超过 1%，需要排查和修复",
                        priority="P1",
                        source="system_health",
                        data_support={"error_rate": error_rate * 100},
                        target_agent="backend",
                    ))

        return ImprovementSuggestions(suggestions=suggestions)

    def generate_alert_summary(
        self,
        ops_task: OpsTask,
        exception_data: ExceptionData,
        metrics_data: MetricsData,
    ) -> AlertSummary:
        critical = 0
        high = 0
        medium = 0
        low = 0

        alert_by_service: Dict[str, Dict[str, int]] = {}

        for exc in exception_data.exceptions:
            if exc.count > 50:
                critical += 1
            elif exc.count > 20:
                high += 1
            elif exc.count > 5:
                medium += 1
            else:
                low += 1

            svc = exc.service
            if svc not in alert_by_service:
                alert_by_service[svc] = {"crash": 0, "performance": 0, "error": 0, "availability": 0}
            if exc.type in alert_by_service[svc]:
                alert_by_service[svc][exc.type] += exc.count

        for svc_name, svc_metrics in metrics_data.services.items():
            if svc_metrics.http_request_duration_p95 > 1.0:
                high += 1
                if svc_name not in alert_by_service:
                    alert_by_service[svc_name] = {"crash": 0, "performance": 0, "error": 0, "availability": 0}
                alert_by_service[svc_name]["performance"] += 1

        total = critical + high + medium + low

        increasing = []
        decreasing = []
        stable = []
        for svc_name in alert_by_service:
            total_svc_alerts = sum(alert_by_service[svc_name].values())
            if total_svc_alerts > 30:
                increasing.append(f"{svc_name}_errors")
            elif total_svc_alerts > 10:
                stable.append(f"{svc_name}_errors")
            else:
                decreasing.append(f"{svc_name}_errors")

        top_alerts = []
        for svc_name, types in alert_by_service.items():
            for alert_type, count in types.items():
                if count > 0:
                    top_alerts.append(TopAlert(service=svc_name, type=alert_type, count=count))
        top_alerts.sort(key=lambda x: x.count, reverse=True)
        top_alerts = top_alerts[:10]

        summary_data = AlertSummaryData(
            timestamp=datetime.now(timezone.utc).isoformat(),
            period=ops_task.period,
            alerts=AlertCounts(
                total=total,
                critical=critical,
                high=high,
                medium=medium,
                low=low,
            ),
            trends=AlertTrends(
                increasing=increasing,
                decreasing=decreasing,
                stable=stable,
            ),
            top_alerts=top_alerts,
        )

        return AlertSummary(alert_summary=summary_data)

    def generate_health_report(
        self,
        metrics_data: MetricsData,
        exception_data: ExceptionData,
    ) -> HealthReport:
        services_health: Dict[str, ServiceHealth] = {}
        overall_issues: List[str] = []
        degraded_count = 0
        unhealthy_count = 0

        for svc_name, svc_metrics in metrics_data.services.items():
            issues: List[str] = []

            if svc_metrics.http_requests_total > 0:
                error_rate = (svc_metrics.http_errors_total / svc_metrics.http_requests_total) * 100
            else:
                error_rate = 0.0

            latency_p95 = svc_metrics.http_request_duration_p95

            svc_exceptions = [e for e in exception_data.exceptions if e.service == svc_name]
            exception_count = sum(e.count for e in svc_exceptions)

            if error_rate > 5.0 or latency_p95 > 3.0 or exception_count > 50:
                status = "unhealthy"
                unhealthy_count += 1
            elif error_rate > 1.0 or latency_p95 > 1.0 or exception_count > 10:
                status = "degraded"
                degraded_count += 1
            else:
                status = "healthy"

            if error_rate > 1.0:
                issues.append(f"错误率过高: {error_rate:.2f}%")
            if latency_p95 > 1.0:
                issues.append(f"P95延迟过高: {latency_p95:.2f}s")
            if exception_count > 10:
                issues.append(f"异常次数过多: {exception_count}")

            if status != "healthy":
                overall_issues.append(f"{svc_name}: {status}")

            services_health[svc_name] = ServiceHealth(
                status=status,
                error_rate=round(error_rate, 2),
                latency_p95=round(latency_p95, 3),
                issues=issues,
            )

        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        report_data = HealthReportData(
            timestamp=datetime.now(timezone.utc).isoformat(),
            services=services_health,
            overall_status=overall_status,
            issues=overall_issues,
        )

        return HealthReport(health_report=report_data)

    def extract_insights(
        self,
        analytics_data: Optional[Dict[str, Any]] = None,
        insight_types: Optional[List[str]] = None,
        min_quality_score: float = 0.6,
        max_insights: int = 10,
    ) -> Dict[str, Any]:
        """从分析数据中提取洞察

        Args:
            analytics_data: 分析数据（模拟数据）
            insight_types: 洞察类型列表
            min_quality_score: 最小质量评分
            max_insights: 最大洞察数量

        Returns:
            洞察提取结果
        """
        if insight_types is None:
            insight_types = ["player_behavior", "region_heat", "quest_completion", "vote_tendency", "economy"]

        if analytics_data is None:
            analytics_data = {
                "daily_active_users": 1200,
                "vote_participation_rate": 0.65,
                "quest_completion_rate": 0.72,
                "region_visits": {
                    "region_iron_guard": 850,
                    "region_ash_valley": 620,
                },
                "top_quests": ["quest_rescue_01", "quest_blacksmith_01"],
                "npc_interactions": {"npc_blacksmith_01": 320, "npc_farmer_01": 280},
            }

        insights: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        insight_templates: List[Dict[str, Any]] = [
            {
                "type": "player_behavior",
                "title": "玩家参与度呈上升趋势",
                "description": "过去7天日活跃用户增长15%，投票参与率稳定在65%以上",
                "confidence": 0.85,
                "impact": 0.7,
                "novelty": 0.6,
            },
            {
                "type": "region_heat",
                "title": "铁卫城周边区域访问量最高",
                "description": "铁卫城周边区域访问量占总访问量的58%，灰谷废墟占比42%",
                "confidence": 0.92,
                "impact": 0.75,
                "novelty": 0.4,
            },
            {
                "type": "quest_completion",
                "title": "主线任务完成率高于支线",
                "description": "主线任务平均完成率85%，支线任务平均完成率62%，建议增加支线吸引力",
                "confidence": 0.88,
                "impact": 0.65,
                "novelty": 0.55,
            },
            {
                "type": "vote_tendency",
                "title": "玩家偏好探索向内容",
                "description": "近三轮投票中，探索新区域类候选平均得票率最高（45%），战斗类仅20%",
                "confidence": 0.78,
                "impact": 0.8,
                "novelty": 0.7,
            },
            {
                "type": "economy",
                "title": "金币产出消耗基本平衡",
                "description": "玩家日均金币收入约500，消耗约450，经济系统处于健康区间",
                "confidence": 0.82,
                "impact": 0.6,
                "novelty": 0.5,
            },
        ]

        for template in insight_templates:
            if template["type"] not in insight_types:
                continue

            confidence = float(template["confidence"])
            impact = float(template["impact"])
            novelty = float(template["novelty"])

            quality_score = (
                confidence * 0.3
                + impact * 0.35
                + novelty * 0.2
                + random.uniform(0, 0.15)
            )

            if quality_score < min_quality_score:
                continue

            insight = {
                "insight_id": f"insight_{uuid.uuid4().hex[:8]}",
                "type": template["type"],
                "title": template["title"],
                "description": template["description"],
                "confidence": round(confidence, 2),
                "impact": round(impact, 2),
                "novelty": round(novelty, 2),
                "quality_score": round(quality_score, 3),
                "source_data": {"analytics_report_id": "report_daily_20260709"},
                "created_at": now,
            }
            insights.append(insight)

            if len(insights) >= max_insights:
                break

        insights.sort(key=lambda x: x["quality_score"], reverse=True)

        return {
            "insights_count": len(insights),
            "insights": insights,
            "quality_distribution": {
                "high": sum(1 for i in insights if i["quality_score"] >= 0.8),
                "medium": sum(1 for i in insights if 0.6 <= i["quality_score"] < 0.8),
                "low": sum(1 for i in insights if i["quality_score"] < 0.6),
            },
            "generated_at": now,
        }

    def generate_requirements(
        self,
        insights: Optional[List[Dict[str, Any]]] = None,
        target_scope: str = "world",
        priority_threshold: str = "P2",
        max_requirements: int = 10,
    ) -> Dict[str, Any]:
        """根据洞察生成需求包

        Args:
            insights: 洞察列表
            target_scope: 目标范围
            priority_threshold: 优先级阈值
            max_requirements: 最大需求数量

        Returns:
            需求生成结果
        """
        if insights is None:
            extraction_result = self.extract_insights()
            insights = extraction_result["insights"]

        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        threshold_level = priority_order.get(priority_threshold, 2)

        requirements: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        for insight in insights:
            quality = insight["quality_score"]
            if quality >= 0.85:
                priority = "P0"
            elif quality >= 0.75:
                priority = "P1"
            elif quality >= 0.65:
                priority = "P2"
            else:
                priority = "P3"

            if priority_order.get(priority, 3) > threshold_level:
                continue

            req_type = insight["type"]
            if req_type == "player_behavior":
                title = f"增加{insight['title'][:10]}相关的玩家引导内容"
                description = f"基于玩家行为洞察：{insight['description']}，建议优化新手引导和日常任务系统"
                scope = "quest"
                effort = "2人日"
                acceptance = [
                    "新手引导流程优化完成",
                    "日常任务系统调整完成",
                    "玩家留存率提升5%",
                ]
            elif req_type == "region_heat":
                title = "为热门区域增加更多探索内容"
                description = f"基于区域热度洞察：{insight['description']}，建议在高访问量区域增加支线任务和隐藏内容"
                scope = "world"
                effort = "3人日"
                acceptance = [
                    "新增3个支线任务",
                    "新增2个隐藏区域",
                    "区域停留时间提升10%",
                ]
            elif req_type == "quest_completion":
                title = "优化支线任务设计提升完成率"
                description = f"基于任务完成率洞察：{insight['description']}，建议优化支线任务的引导和奖励设计"
                scope = "quest"
                effort = "2人日"
                acceptance = [
                    "支线任务引导优化完成",
                    "支线奖励体系调整完成",
                    "支线完成率提升至70%",
                ]
            elif req_type == "vote_tendency":
                title = "增加探索向内容生成比例"
                description = f"基于投票倾向洞察：{insight['description']}，建议在后续内容生成中增加探索类内容占比"
                scope = "world"
                effort = "1人日"
                acceptance = [
                    "内容生成模板调整完成",
                    "探索类内容占比提升至50%",
                    "投票参与率保持稳定",
                ]
            elif req_type == "economy":
                title = "优化经济系统增加金币消耗途径"
                description = f"基于经济洞察：{insight['description']}，建议增加更多金币消耗途径以维持经济平衡"
                scope = "world"
                effort = "2人日"
                acceptance = [
                    "新增2个金币消耗系统",
                    "经济系统保持平衡",
                    "玩家满意度不下降",
                ]
            else:
                continue

            quality_score = quality * 0.9 + random.uniform(0, 0.1)

            requirement = {
                "requirement_id": f"req_{uuid.uuid4().hex[:8]}",
                "title": title,
                "description": description,
                "priority": priority,
                "target_scope": scope,
                "estimated_effort": effort,
                "acceptance_criteria": acceptance,
                "source_insight_ids": [insight["insight_id"]],
                "quality_score": round(quality_score, 3),
                "status": "draft",
                "created_at": now,
            }

            if target_scope == "all" or scope == target_scope:
                requirements.append(requirement)

        requirements.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["quality_score"]))

        requirements = requirements[:max_requirements]

        return {
            "requirements_count": len(requirements),
            "requirements": requirements,
            "priority_distribution": {
                "P0": sum(1 for r in requirements if r["priority"] == "P0"),
                "P1": sum(1 for r in requirements if r["priority"] == "P1"),
                "P2": sum(1 for r in requirements if r["priority"] == "P2"),
                "P3": sum(1 for r in requirements if r["priority"] == "P3"),
            },
            "generated_at": now,
        }

    def execute_insight_extraction(
        self,
        task_id: str = "",
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Orchestrator 调用入口：洞察提取任务"""
        if params is None:
            params = {}

        return self.extract_insights(
            insight_types=params.get("insight_types"),
            min_quality_score=params.get("min_quality_score", 0.6),
            max_insights=params.get("max_insights", 10),
        )

    def execute_requirement_generation(
        self,
        task_id: str = "",
        params: Optional[Dict[str, Any]] = None,
        input_from_insight_task: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Orchestrator 调用入口：需求生成任务

        支持从上游洞察提取任务获取输入
        """
        if params is None:
            params = {}

        insights = None
        if input_from_insight_task and "insights" in input_from_insight_task:
            insights = input_from_insight_task["insights"]

        return self.generate_requirements(
            insights=insights,
            target_scope=params.get("target_scope", "world"),
            priority_threshold=params.get("priority_threshold", "P2"),
            max_requirements=params.get("max_requirements", 10),
        )

    def execute_ops_workflow(
        self,
        ops_task: OpsTask,
        metrics_data: Optional[MetricsData] = None,
        exception_data: Optional[ExceptionData] = None,
        log_data: Optional[LogData] = None,
        feedback_data: Optional[FeedbackData] = None,
    ) -> OpsResult:
        try:
            if metrics_data is None:
                metrics_data = self.collect_metrics(ops_task)

            if exception_data is None:
                exception_data = ExceptionData(exceptions=[])

            if log_data is None:
                log_data = LogData(logs=[])

            if feedback_data is None:
                feedback_data = FeedbackData(feedback_items=[])

            exception_report = self.generate_exception_report(ops_task, exception_data)

            improvement_suggestions = self.form_improvement_suggestions(
                exception_report, metrics_data, feedback_data
            )

            alert_summary = self.generate_alert_summary(ops_task, exception_data, metrics_data)

            health_report = self.generate_health_report(metrics_data, exception_data)

            return OpsResult(
                success=True,
                exception_report=exception_report,
                improvement_suggestions=improvement_suggestions,
                alert_summary=alert_summary,
                health_report=health_report,
                message="运维分析工作流执行完成"
            )
        except Exception as e:
            self.error_handler.handle_error("workflow", str(e))
            return OpsResult(
                success=False,
                exception_report=None,
                improvement_suggestions=None,
                alert_summary=None,
                health_report=None,
                message=f"运维分析工作流执行失败: {str(e)}"
            )
