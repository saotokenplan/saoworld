import argparse
import json
from datetime import date
from product_agent import ProductAgent
from product_input_schemas import (
    VersionStatus,
    VoteResults,
    OnlineMetrics,
    IssueList,
    VoteResult,
    TrendData,
    Issue,
)


def _parse_date(date_str: str) -> date:
    return date.fromisoformat(date_str)


def _load_version_status(args) -> VersionStatus:
    return VersionStatus(
        version=args.version,
        status=args.status,
        completed_tasks=args.completed_tasks,
        total_tasks=args.total_tasks,
        blockers=args.blockers.split(",") if args.blockers else [],
        milestones=[],
    )


def _load_vote_results(args) -> VoteResults:
    results = []
    if args.vote_results:
        for r in args.vote_results.split(","):
            parts = r.split(":")
            if len(parts) == 3:
                results.append(VoteResult(
                    candidate_id=parts[0],
                    votes=int(parts[1]),
                    percentage=float(parts[2]),
                ))
    return VoteResults(
        vote_cycle_id=args.vote_cycle_id,
        winning_candidate_id=args.winning_candidate_id,
        results=results,
        total_voters=args.total_voters,
    )


def _load_online_metrics(args) -> OnlineMetrics:
    return OnlineMetrics(
        daily_active_users=args.daily_active_users,
        vote_participation_rate=args.vote_participation_rate,
        task_completion_rate=args.task_completion_rate,
        new_content_stay_time=args.new_content_stay_time,
        crash_rate=args.crash_rate,
        trends=TrendData(
            user_growth=args.user_growth,
            engagement=args.engagement,
            content_consumption=args.content_consumption,
        ),
    )


def _load_issue_list(args) -> IssueList:
    issues = []
    if args.issues:
        for i in args.issues.split(","):
            parts = i.split(":")
            if len(parts) == 4:
                issues.append(Issue(
                    id=parts[0],
                    title=parts[1],
                    severity=parts[2],
                    type=parts[3],
                    status="open",
                ))
    return IssueList(issues=issues)


def generate_version_brief(args):
    agent = ProductAgent()
    agent.collect_input_data(
        version_status=_load_version_status(args),
        vote_results=_load_vote_results(args),
        online_metrics=_load_online_metrics(args),
        issue_list=_load_issue_list(args),
    )
    delivery = agent.run(next_version=args.next_version)
    output = json.dumps(delivery, indent=2, ensure_ascii=False, default=str)
    print(output)


def analyze_state(args):
    agent = ProductAgent()
    agent.collect_input_data(
        version_status=_load_version_status(args),
        vote_results=_load_vote_results(args),
        online_metrics=_load_online_metrics(args),
        issue_list=_load_issue_list(args),
    )
    analysis = agent.analyze_current_state()
    output = json.dumps(analysis, indent=2, ensure_ascii=False, default=str)
    print(output)


def generate_milestone_plan(args):
    agent = ProductAgent()
    agent.collect_input_data(
        version_status=_load_version_status(args),
        vote_results=_load_vote_results(args),
        online_metrics=_load_online_metrics(args),
        issue_list=_load_issue_list(args),
    )
    goals = ["示例目标"]
    matrix = agent.decompose_and_prioritize(args.next_version, goals)
    plan = agent.generate_milestone_plan(args.next_version, matrix.tasks)
    output = json.dumps(plan.dict(), indent=2, ensure_ascii=False, default=str)
    print(output)


def main():
    parser = argparse.ArgumentParser(description="Product Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument("--version", default="0.1.0", help="当前版本")
    common_args.add_argument("--status", default="completed", help="版本状态")
    common_args.add_argument("--completed-tasks", type=int, default=60, help="已完成任务数")
    common_args.add_argument("--total-tasks", type=int, default=60, help="总任务数")
    common_args.add_argument("--blockers", default="", help="阻塞问题列表")
    common_args.add_argument("--vote-cycle-id", default="vc_20260701", help="投票周期ID")
    common_args.add_argument("--winning-candidate-id", default="candidate_001", help="获胜候选项")
    common_args.add_argument("--vote-results", default="", help="投票结果")
    common_args.add_argument("--total-voters", type=int, default=500, help="总投票数")
    common_args.add_argument("--daily-active-users", type=int, default=1000, help="日活用户数")
    common_args.add_argument("--vote-participation-rate", type=float, default=0.65, help="投票参与率")
    common_args.add_argument("--task-completion-rate", type=float, default=0.72, help="任务完成率")
    common_args.add_argument("--new-content-stay-time", type=int, default=45, help="新内容停留时间")
    common_args.add_argument("--crash-rate", type=float, default=0.01, help="崩溃率")
    common_args.add_argument("--user-growth", default="stable", help="用户增长趋势")
    common_args.add_argument("--engagement", default="stable", help="参与度趋势")
    common_args.add_argument("--content-consumption", default="up", help="内容消费趋势")
    common_args.add_argument("--issues", default="", help="问题列表")

    gen_brief_parser = subparsers.add_parser(
        "generate-version-brief", parents=[common_args], help="生成版本需求文档"
    )
    gen_brief_parser.add_argument("--next-version", default="0.2.0", help="下一版本号")
    gen_brief_parser.set_defaults(func=generate_version_brief)

    analyze_parser = subparsers.add_parser(
        "analyze-state", parents=[common_args], help="分析当前状态"
    )
    analyze_parser.set_defaults(func=analyze_state)

    gen_milestone_parser = subparsers.add_parser(
        "generate-milestone-plan", parents=[common_args], help="生成里程碑计划"
    )
    gen_milestone_parser.add_argument("--next-version", default="0.2.0", help="下一版本号")
    gen_milestone_parser.set_defaults(func=generate_milestone_plan)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
