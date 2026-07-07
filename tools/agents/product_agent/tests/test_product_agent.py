import pytest
from datetime import date
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from product_agent import ProductAgent
from input_schemas import (
    VersionStatus,
    VoteResults,
    OnlineMetrics,
    IssueList,
    InputMilestone,
    VoteResult,
    TrendData,
    Issue,
)
from output_schemas import PriorityMatrix, MilestonePlan, VersionBrief, Task, OutputMilestone
from error_handler import ErrorHandler, InputMissingError


class TestInputSchemas:
    def test_version_status(self):
        milestone = InputMilestone(id="M1", name="测试里程碑", due_date=date(2026, 7, 10), completed=True)
        status = VersionStatus(
            version="0.1.0",
            status="in_progress",
            completed_tasks=45,
            total_tasks=60,
            blockers=["BLOCKER-001"],
            milestones=[milestone],
        )
        assert status.version == "0.1.0"
        assert status.completed_tasks == 45
        assert len(status.milestones) == 1

    def test_vote_results(self):
        results = VoteResults(
            vote_cycle_id="vc_20260701",
            winning_candidate_id="candidate_001",
            results=[
                VoteResult(candidate_id="candidate_001", votes=200, percentage=40.0),
                VoteResult(candidate_id="candidate_002", votes=150, percentage=30.0),
            ],
            total_voters=500,
        )
        assert results.winning_candidate_id == "candidate_001"
        assert len(results.results) == 2

    def test_online_metrics(self):
        metrics = OnlineMetrics(
            daily_active_users=1200,
            vote_participation_rate=0.65,
            task_completion_rate=0.72,
            new_content_stay_time=45,
            crash_rate=0.015,
            trends=TrendData(user_growth="up", engagement="stable", content_consumption="up"),
        )
        assert metrics.daily_active_users == 1200
        assert metrics.trends.user_growth == "up"

    def test_issue_list(self):
        issues = IssueList(
            issues=[
                Issue(id="ISSUE-001", title="测试问题", severity="high", type="bug", status="open"),
            ]
        )
        assert len(issues.issues) == 1
        assert issues.issues[0].severity == "high"


class TestOutputSchemas:
    def test_task(self):
        task = Task(
            id="TASK-001",
            title="测试任务",
            priority="P0",
            size="small",
            dependencies=[],
            estimated_hours=4.0,
            assignee="backend",
        )
        assert task.priority == "P0"
        assert task.estimated_hours == 4.0

    def test_priority_matrix(self):
        tasks = [Task(
            id="TASK-001",
            title="测试任务",
            priority="P0",
            size="small",
            dependencies=[],
            estimated_hours=4.0,
            assignee="backend",
        )]
        matrix = PriorityMatrix(version="0.2.0", tasks=tasks)
        assert matrix.version == "0.2.0"
        assert len(matrix.tasks) == 1

    def test_milestone_plan(self):
        milestones = [OutputMilestone(
            id="M1",
            name="测试里程碑",
            due_date=date(2026, 7, 15),
            tasks=["TASK-001"],
            status="pending",
        )]
        plan = MilestonePlan(version="0.2.0", milestones=milestones)
        assert plan.version == "0.2.0"
        assert len(plan.milestones) == 1

    def test_version_brief(self):
        brief = VersionBrief(
            version="0.2.0",
            goals=["目标1", "目标2"],
            not_goals=["不做1"],
            core_metrics=["指标1"],
            key_risks=["风险1"],
            risk_mitigation=["缓解1"],
            acceptance_criteria=["验收1"],
            created_at=date.today(),
        )
        assert len(brief.goals) == 2
        assert brief.created_at == date.today()


class TestErrorHandler:
    def test_validate_input_completeness(self):
        inputs = {"a": 1, "b": 2}
        result = ErrorHandler.validate_input_completeness(inputs)
        assert result is True

        inputs_missing = {"a": None, "b": 2}
        result = ErrorHandler.validate_input_completeness(inputs_missing)
        assert result is False

    def test_handle_input_missing_with_default(self):
        result = ErrorHandler.handle_input_missing("test", "default")
        assert result == "default"

    def test_handle_input_missing_no_default(self):
        with pytest.raises(InputMissingError):
            ErrorHandler.handle_input_missing("test")

    def test_handle_data_conflict(self):
        result = ErrorHandler.handle_data_conflict("test_conflict")
        assert result == "vote_results"


class TestProductAgent:
    def test_collect_input_data(self):
        agent = ProductAgent()
        status = VersionStatus(version="0.1.0", status="completed", completed_tasks=60, total_tasks=60)
        agent.collect_input_data(version_status=status)
        assert agent.version_status == status

    def test_analyze_current_state_with_version_status(self):
        agent = ProductAgent()
        milestone = InputMilestone(id="M1", name="测试", due_date=date(2026, 7, 10), completed=True)
        status = VersionStatus(
            version="0.1.0",
            status="in_progress",
            completed_tasks=45,
            total_tasks=60,
            blockers=["BLOCKER-001"],
            milestones=[milestone],
        )
        agent.collect_input_data(version_status=status)
        analysis = agent.analyze_current_state()
        assert analysis["version_progress"] == 75.0
        assert analysis["has_blockers"] is True

    def test_analyze_current_state_with_vote_results(self):
        agent = ProductAgent()
        results = VoteResults(
            vote_cycle_id="vc_20260701",
            winning_candidate_id="candidate_001",
            results=[VoteResult(candidate_id="candidate_001", votes=200, percentage=40.0)],
            total_voters=500,
        )
        agent.collect_input_data(vote_results=results)
        analysis = agent.analyze_current_state()
        assert analysis["winning_candidate"] == "candidate_001"
        assert analysis["total_voters"] == 500

    def test_determine_version_goals_with_critical_issues(self):
        agent = ProductAgent()
        issues = IssueList(
            issues=[Issue(id="ISSUE-001", title="严重问题", severity="critical", type="bug", status="open")]
        )
        agent.collect_input_data(issue_list=issues)
        analysis = agent.analyze_current_state()
        goals = agent.determine_version_goals(analysis)
        assert "修复所有 critical 级别问题" in goals

    def test_determine_version_goals_with_high_crash_rate(self):
        agent = ProductAgent()
        metrics = OnlineMetrics(
            daily_active_users=1000,
            vote_participation_rate=0.65,
            task_completion_rate=0.72,
            new_content_stay_time=45,
            crash_rate=0.02,
            trends=TrendData(user_growth="stable", engagement="stable", content_consumption="stable"),
        )
        agent.collect_input_data(online_metrics=metrics)
        analysis = agent.analyze_current_state()
        goals = agent.determine_version_goals(analysis)
        assert "降低崩溃率至 1% 以下" in goals

    def test_generate_version_brief(self):
        agent = ProductAgent()
        goals = ["目标1", "目标2"]
        brief = agent.generate_version_brief("0.2.0", goals)
        assert brief.version == "0.2.0"
        assert len(brief.goals) == 2
        assert len(brief.not_goals) > 0
        assert len(brief.core_metrics) > 0

    def test_decompose_and_prioritize_with_critical_issues(self):
        agent = ProductAgent()
        issues = IssueList(
            issues=[Issue(id="ISSUE-001", title="严重bug", severity="critical", type="bug", status="open")]
        )
        agent.collect_input_data(issue_list=issues)
        matrix = agent.decompose_and_prioritize("0.2.0", ["修复问题"])
        assert len(matrix.tasks) >= 1
        p0_tasks = [t for t in matrix.tasks if t.priority == "P0"]
        assert len(p0_tasks) >= 1

    def test_decompose_and_prioritize_with_vote_results(self):
        agent = ProductAgent()
        results = VoteResults(
            vote_cycle_id="vc_20260701",
            winning_candidate_id="candidate_001",
            results=[VoteResult(candidate_id="candidate_001", votes=200, percentage=40.0)],
            total_voters=500,
        )
        agent.collect_input_data(vote_results=results)
        matrix = agent.decompose_and_prioritize("0.2.0", ["实现投票选项"])
        assert len(matrix.tasks) >= 1
        has_vote_task = any("实现投票获胜选项" in t.title for t in matrix.tasks)
        assert has_vote_task is True

    def test_generate_milestone_plan(self):
        agent = ProductAgent()
        tasks = [
            Task(id="TASK-001", title="P0任务", priority="P0", size="small", dependencies=[], estimated_hours=4.0, assignee="backend"),
            Task(id="TASK-002", title="P1任务", priority="P1", size="medium", dependencies=[], estimated_hours=8.0, assignee="world"),
            Task(id="TASK-003", title="P2任务", priority="P2", size="small", dependencies=[], estimated_hours=4.0, assignee="qa"),
        ]
        plan = agent.generate_milestone_plan("0.2.0", tasks)
        assert len(plan.milestones) == 3
        assert plan.milestones[0].id == "M1"
        assert plan.milestones[1].id == "M2"
        assert plan.milestones[2].id == "M3"

    def test_run_full_flow(self):
        agent = ProductAgent()
        status = VersionStatus(version="0.1.0", status="completed", completed_tasks=60, total_tasks=60)
        results = VoteResults(
            vote_cycle_id="vc_20260701",
            winning_candidate_id="candidate_001",
            results=[VoteResult(candidate_id="candidate_001", votes=200, percentage=40.0)],
            total_voters=500,
        )
        metrics = OnlineMetrics(
            daily_active_users=1000,
            vote_participation_rate=0.65,
            task_completion_rate=0.72,
            new_content_stay_time=45,
            crash_rate=0.01,
            trends=TrendData(user_growth="stable", engagement="stable", content_consumption="stable"),
        )
        agent.collect_input_data(version_status=status, vote_results=results, online_metrics=metrics)
        delivery = agent.run("0.2.0")
        assert "version_brief" in delivery
        assert "priority_matrix" in delivery
        assert "milestone_plan" in delivery
        assert "delivered_at" in delivery

    def test_run_with_empty_goals(self):
        agent = ProductAgent()
        status = VersionStatus(version="0.1.0", status="completed", completed_tasks=60, total_tasks=60)
        agent.collect_input_data(version_status=status)
        delivery = agent.run("0.2.0")
        assert "version_brief" in delivery
        brief = delivery["version_brief"]
        assert "维护当前版本稳定性" in brief["goals"]
