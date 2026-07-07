from datetime import date, timedelta
from typing import List, Optional, Dict, Any
import structlog
from input_schemas import (
    VersionStatus,
    VoteResults,
    OnlineMetrics,
    IssueList,
    Roadmap,
    VisionDocument,
)
from output_schemas import PriorityMatrix, MilestonePlan, VersionBrief, Task, OutputMilestone
from error_handler import ErrorHandler

logger = structlog.get_logger()


class ProductAgent:
    def __init__(self):
        self.version_status: Optional[VersionStatus] = None
        self.vote_results: Optional[VoteResults] = None
        self.online_metrics: Optional[OnlineMetrics] = None
        self.issue_list: Optional[IssueList] = None
        self.roadmap: Optional[Roadmap] = None
        self.vision: Optional[VisionDocument] = None
        self.error_handler = ErrorHandler()

    def collect_input_data(
        self,
        version_status: Optional[VersionStatus] = None,
        vote_results: Optional[VoteResults] = None,
        online_metrics: Optional[OnlineMetrics] = None,
        issue_list: Optional[IssueList] = None,
        roadmap: Optional[Roadmap] = None,
        vision: Optional[VisionDocument] = None,
    ) -> None:
        self.version_status = version_status
        self.vote_results = vote_results
        self.online_metrics = online_metrics
        self.issue_list = issue_list
        self.roadmap = roadmap
        self.vision = vision
        logger.info("input_data_collected")

    def analyze_current_state(self) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {}

        if self.version_status:
            progress = (self.version_status.completed_tasks / self.version_status.total_tasks) * 100 if self.version_status.total_tasks > 0 else 0
            analysis["version_progress"] = round(progress, 1)
            analysis["has_blockers"] = len(self.version_status.blockers) > 0
            analysis["blockers_count"] = len(self.version_status.blockers)
            analysis["completed_milestones"] = sum(1 for m in self.version_status.milestones if m.completed)
            analysis["total_milestones"] = len(self.version_status.milestones)

        if self.vote_results:
            analysis["winning_candidate"] = self.vote_results.winning_candidate_id
            analysis["total_voters"] = self.vote_results.total_voters
            analysis["vote_distribution"] = {r.candidate_id: r.percentage for r in self.vote_results.results}

        if self.online_metrics:
            analysis["daily_active_users"] = self.online_metrics.daily_active_users
            analysis["vote_participation_rate"] = self.online_metrics.vote_participation_rate
            analysis["task_completion_rate"] = self.online_metrics.task_completion_rate
            analysis["trends"] = self.online_metrics.trends.model_dump()
            analysis["crash_rate"] = self.online_metrics.crash_rate

        if self.issue_list:
            critical_issues = [i for i in self.issue_list.issues if i.severity == "critical"]
            high_issues = [i for i in self.issue_list.issues if i.severity == "high"]
            open_issues = [i for i in self.issue_list.issues if i.status == "open"]
            analysis["critical_issues_count"] = len(critical_issues)
            analysis["high_issues_count"] = len(high_issues)
            analysis["open_issues_count"] = len(open_issues)
            analysis["issue_summary"] = {i.id: i.title for i in open_issues[:10]}

        logger.info("state_analysis_complete", analysis=analysis)
        return analysis

    def determine_version_goals(self, analysis: Dict[str, Any]) -> List[str]:
        goals: List[str] = []

        if analysis.get("critical_issues_count", 0) > 0:
            goals.append("修复所有 critical 级别问题")

        if analysis.get("high_issues_count", 0) > 0:
            goals.append("修复主要 high 级别问题")

        if "crash_rate" in analysis and analysis["crash_rate"] > 0.01:
            goals.append("降低崩溃率至 1% 以下")

        if "vote_participation_rate" in analysis and analysis["vote_participation_rate"] < 0.6:
            goals.append("提升投票参与率至 60% 以上")

        if analysis.get("winning_candidate"):
            goals.append(f"实现投票获胜选项: {analysis['winning_candidate']}")

        if self.roadmap and self.roadmap.current_phase:
            goals.append(f"完成路线图阶段: {self.roadmap.current_phase}")

        goals = list(dict.fromkeys(goals))

        logger.info("version_goals_determined", goals=goals)
        return goals

    def generate_version_brief(self, version: str, goals: List[str]) -> VersionBrief:
        not_goals = [
            "不新增大规模游戏玩法系统",
            "不重构核心架构",
            "不扩展到新平台",
        ]

        core_metrics = [
            "投票参与率 >= 60%",
            "任务完成率 >= 75%",
            "崩溃率 <= 1%",
            "新内容停留时间 >= 40分钟",
        ]

        key_risks = []
        risk_mitigation = []

        if self.version_status and len(self.version_status.blockers) > 0:
            key_risks.append("当前版本存在阻塞问题可能影响进度")
            risk_mitigation.append("优先解决阻塞问题，重新评估时间线")

        if self.online_metrics and self.online_metrics.crash_rate > 0.01:
            key_risks.append("线上崩溃率过高可能影响玩家体验")
            risk_mitigation.append("将稳定性修复列为 P0 优先级")

        acceptance_criteria = [
            "所有 critical 问题已修复",
            "核心功能测试覆盖率 >= 80%",
            "性能指标达标",
            "版本文档完整",
            "灰度发布验证通过",
        ]

        brief = VersionBrief(
            version=version,
            goals=goals,
            not_goals=not_goals,
            core_metrics=core_metrics,
            key_risks=key_risks,
            risk_mitigation=risk_mitigation,
            acceptance_criteria=acceptance_criteria,
            created_at=date.today(),
        )

        logger.info("version_brief_generated", version=version)
        return brief

    def decompose_and_prioritize(self, version: str, goals: List[str]) -> PriorityMatrix:
        tasks: List[Task] = []
        task_id = 1

        critical_issues = []
        high_issues = []
        if self.issue_list:
            critical_issues = [i for i in self.issue_list.issues if i.severity == "critical" and i.status == "open"]
            high_issues = [i for i in self.issue_list.issues if i.severity == "high" and i.status == "open"]

        for issue in critical_issues:
            tasks.append(Task(
                id=f"TASK-{task_id:03d}",
                title=f"修复关键问题: {issue.title}",
                priority="P0",
                size="small" if issue.type == "bug" else "medium",
                dependencies=[],
                estimated_hours=4.0 if issue.type == "bug" else 8.0,
                assignee="backend" if issue.type in ["bug", "performance"] else "content",
                description=f"问题ID: {issue.id}, 类型: {issue.type}",
            ))
            task_id += 1

        if self.online_metrics and self.online_metrics.crash_rate > 0.01:
            tasks.append(Task(
                id=f"TASK-{task_id:03d}",
                title="优化稳定性，降低崩溃率",
                priority="P0",
                size="medium",
                dependencies=[],
                estimated_hours=16.0,
                assignee="backend",
            ))
            task_id += 1

        for issue in high_issues[:3]:
            tasks.append(Task(
                id=f"TASK-{task_id:03d}",
                title=f"修复重要问题: {issue.title}",
                priority="P1",
                size="small" if issue.type == "bug" else "medium",
                dependencies=[],
                estimated_hours=4.0 if issue.type == "bug" else 8.0,
                assignee="backend" if issue.type in ["bug", "performance"] else "content",
                description=f"问题ID: {issue.id}, 类型: {issue.type}",
            ))
            task_id += 1

        if self.vote_results:
            tasks.append(Task(
                id=f"TASK-{task_id:03d}",
                title=f"实现投票获胜选项: {self.vote_results.winning_candidate_id}",
                priority="P1",
                size="large",
                dependencies=[],
                estimated_hours=40.0,
                assignee="world",
            ))
            task_id += 1

        if self.online_metrics and self.online_metrics.vote_participation_rate < 0.6:
            tasks.append(Task(
                id=f"TASK-{task_id:03d}",
                title="优化投票流程，提升参与率",
                priority="P1",
                size="medium",
                dependencies=[],
                estimated_hours=16.0,
                assignee="game",
            ))
            task_id += 1

        tasks.append(Task(
            id=f"TASK-{task_id:03d}",
            title="编写版本测试用例",
            priority="P2",
            size="medium",
            dependencies=[],
            estimated_hours=12.0,
            assignee="qa",
        ))
        task_id += 1

        tasks.append(Task(
            id=f"TASK-{task_id:03d}",
            title="执行灰度发布验证",
            priority="P2",
            size="small",
            dependencies=[f"TASK-{task_id-1:03d}"],
            estimated_hours=8.0,
            assignee="ops",
        ))
        task_id += 1

        matrix = PriorityMatrix(version=version, tasks=tasks)
        logger.info("priority_matrix_generated", task_count=len(tasks))
        return matrix

    def generate_milestone_plan(self, version: str, tasks: List[Task]) -> MilestonePlan:
        today = date.today()
        milestones: List[OutputMilestone] = []

        p0_tasks = [t for t in tasks if t.priority == "P0"]
        p1_tasks = [t for t in tasks if t.priority == "P1"]
        p2_tasks = [t for t in tasks if t.priority == "P2"]

        if p0_tasks:
            p0_ids = [t.id for t in p0_tasks]
            milestones.append(OutputMilestone(
                id="M1",
                name="关键修复完成",
                due_date=today + timedelta(days=5),
                tasks=p0_ids,
                status="pending",
            ))

        if p1_tasks:
            p1_ids = [t.id for t in p1_tasks]
            milestones.append(OutputMilestone(
                id="M2",
                name="核心功能实现",
                due_date=today + timedelta(days=15),
                tasks=p1_ids,
                status="pending",
            ))

        if p2_tasks:
            p2_ids = [t.id for t in p2_tasks]
            milestones.append(OutputMilestone(
                id="M3",
                name="测试与发布",
                due_date=today + timedelta(days=20),
                tasks=p2_ids,
                status="pending",
            ))

        plan = MilestonePlan(version=version, milestones=milestones)
        logger.info("milestone_plan_generated", milestone_count=len(milestones))
        return plan

    def deliver_to_system_designer(
        self,
        version_brief: VersionBrief,
        priority_matrix: PriorityMatrix,
        milestone_plan: MilestonePlan,
    ) -> Dict[str, Any]:
        delivery = {
            "version_brief": version_brief.model_dump(),
            "priority_matrix": priority_matrix.model_dump(),
            "milestone_plan": milestone_plan.model_dump(),
            "delivered_at": date.today().isoformat(),
        }
        logger.info("delivered_to_system_designer", version=version_brief.version)
        return delivery

    def run(self, next_version: str = "0.2.0") -> Dict[str, Any]:
        logger.info("product_agent_started", version=next_version)

        inputs = {
            "version_status": self.version_status,
            "vote_results": self.vote_results,
            "online_metrics": self.online_metrics,
        }

        self.error_handler.validate_input_completeness(inputs)

        analysis = self.analyze_current_state()
        goals = self.determine_version_goals(analysis)

        if not goals:
            goals = ["维护当前版本稳定性"]

        version_brief = self.generate_version_brief(next_version, goals)
        priority_matrix = self.decompose_and_prioritize(next_version, goals)
        milestone_plan = self.generate_milestone_plan(next_version, priority_matrix.tasks)

        delivery = self.deliver_to_system_designer(version_brief, priority_matrix, milestone_plan)

        logger.info("product_agent_completed", version=next_version)
        return delivery
