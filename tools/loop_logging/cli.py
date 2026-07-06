from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .agent_session_logger import AgentSessionLogger
from .ci_failure_logger import CIFailureLogger
from .prod_incident_logger import ProdIncidentLogger
from .clusterer import FailureClusterer
from .gap_classifier import GapClassifier
from .issue_generator import GateImprovementIssueGenerator
from .threshold_manager import ThresholdManager
from .golden_case_manager import GoldenCaseManager
from .feedback_collector import IssueFeedbackCollector
from .rule_evaluator import RuleEvaluator
from .rule_improvement_generator import RuleImprovementGenerator


def cmd_agent_log(args: argparse.Namespace) -> None:
    logger = AgentSessionLogger(args.log_dir)

    if args.action == "start":
        logger.log_start(
            session_id=args.session_id,
            agent_name=args.agent_name,
            task_id=args.task_id,
            stage=args.stage,
            summary=args.summary,
            repo=args.repo,
        )
        print(f"Agent session started: {args.session_id}")

    elif args.action == "end":
        logger.log_end(
            session_id=args.session_id,
            agent_name=args.agent_name,
            task_id=args.task_id,
            stage=args.stage,
            summary=args.summary,
        )
        print(f"Agent session ended: {args.session_id}")

    elif args.action == "tool-call":
        logger.log_tool_call(
            session_id=args.session_id,
            agent_name=args.agent_name,
            task_id=args.task_id,
            tool_name=args.tool_name,
            tool_args=json.loads(args.tool_args) if args.tool_args else None,
        )
        print(f"Tool call logged: {args.tool_name}")

    elif args.action == "ci-result":
        logger.log_ci_result(
            session_id=args.session_id,
            agent_name=args.agent_name,
            task_id=args.task_id,
            gate_id=args.gate_id,
            gate_name=args.gate_name,
            status=args.status,
            duration_s=args.duration,
            failure_signature=args.failure_signature,
        )
        print(f"CI result logged: {args.gate_name} - {args.status}")

    elif args.action == "error":
        logger.log_error(
            session_id=args.session_id,
            agent_name=args.agent_name,
            task_id=args.task_id,
            stage=args.stage,
            error_message=args.message,
            error_type=args.error_type,
        )
        print(f"Error logged: {args.message}")


def cmd_ci_failure(args: argparse.Namespace) -> None:
    logger = CIFailureLogger(args.log_dir)
    logger.log(
        pipeline_id=args.pipeline_id,
        run_type=args.run_type,
        gate_id=args.gate_id,
        gate_name=args.gate_name,
        status=args.status,
        duration_s=args.duration,
        failure_signature=args.signature,
        branch=args.branch,
        pr_id=args.pr_id,
        commit=args.commit,
        log_excerpt=args.log_excerpt,
        related_task_id=args.task_id,
    )
    print(f"CI failure logged: {args.pipeline_id} - {args.gate_name}")


def cmd_prod_incident(args: argparse.Namespace) -> None:
    logger = ProdIncidentLogger(args.log_dir)
    logger.log(
        env=args.env,
        version=args.version,
        incident_id=args.incident_id,
        severity=args.severity,
        symptom=args.symptom,
        signal=json.loads(args.signal) if args.signal else None,
        rollback=json.loads(args.rollback) if args.rollback else None,
    )
    print(f"Prod incident logged: {args.incident_id} - {args.symptom}")


def cmd_scan(args: argparse.Namespace) -> None:
    ci_logger = CIFailureLogger(args.log_dir)
    prod_logger = ProdIncidentLogger(args.log_dir)

    end_time = datetime.now()
    start_time = end_time - timedelta(days=args.days)

    ci_failures = ci_logger.read_logs(start_time=start_time, end_time=end_time)
    prod_incidents = prod_logger.read_logs(start_time=start_time, end_time=end_time)

    all_failures = ci_failures + prod_incidents

    if not all_failures:
        print("No failures found in the specified time window")
        return

    clusterer = FailureClusterer()
    clusters = clusterer.cluster(all_failures)

    existing_gate_ids = ["G-STATIC-001", "G-STATIC-002", "G-UNIT-001", "G-UNIT-002", "G-UNIT-003", "G-UNIT-004", "G-UNIT-005", "G-UNIT-006", "G-UNIT-007", "G-UNIT-008", "G-UNIT-009", "G-CONTENT-001", "G-CONTENT-002", "G-CONTENT-003", "G-CONTENT-004", "G-E2E-001"]

    classified_gaps = GapClassifier.batch_classify(clusters, existing_gate_ids)

    if not classified_gaps:
        print("No significant gate gaps detected")
        return

    issue_generator = GateImprovementIssueGenerator()
    cluster_dict = {c.signature: c for c in clusters}
    issues = issue_generator.batch_generate(classified_gaps, cluster_dict, all_failures[:10])

    output_dir = Path(args.output_dir or ".trae/loop-log")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"gate_improvement_issues_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for issue in issues:
            f.write(json.dumps(issue.to_dict()) + "\n")

    print(f"Generated {len(issues)} gate improvement issues")
    print(f"Issues written to: {output_file}")

    for issue in issues[:5]:
        print(f"\nPriority: {issue.priority}")
        print(f"Symptom: {issue.symptom}")
        print(f"Gap Type: {issue.gap_type.value}")
        print(f"Gate: {issue.proposed_gate['name']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Loop Engineering Logging CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser.add_argument("--log-dir", default=".trae/loop-log", help="Log directory")

    agent_log_parser = subparsers.add_parser("agent-log", help="Agent session logging")
    agent_log_sub = agent_log_parser.add_subparsers(dest="action", required=True)

    agent_start = agent_log_sub.add_parser("start")
    agent_start.add_argument("--session-id", required=True)
    agent_start.add_argument("--agent-name", required=True)
    agent_start.add_argument("--task-id", required=True)
    agent_start.add_argument("--stage", default="plan")
    agent_start.add_argument("--summary")
    agent_start.add_argument("--repo")

    agent_end = agent_log_sub.add_parser("end")
    agent_end.add_argument("--session-id", required=True)
    agent_end.add_argument("--agent-name", required=True)
    agent_end.add_argument("--task-id", required=True)
    agent_end.add_argument("--stage", required=True)
    agent_end.add_argument("--summary")

    agent_tool = agent_log_sub.add_parser("tool-call")
    agent_tool.add_argument("--session-id", required=True)
    agent_tool.add_argument("--agent-name", required=True)
    agent_tool.add_argument("--task-id", required=True)
    agent_tool.add_argument("--tool-name", required=True)
    agent_tool.add_argument("--tool-args")

    agent_ci = agent_log_sub.add_parser("ci-result")
    agent_ci.add_argument("--session-id", required=True)
    agent_ci.add_argument("--agent-name", required=True)
    agent_ci.add_argument("--task-id", required=True)
    agent_ci.add_argument("--gate-id", required=True)
    agent_ci.add_argument("--gate-name", required=True)
    agent_ci.add_argument("--status", required=True)
    agent_ci.add_argument("--duration", type=float, required=True)
    agent_ci.add_argument("--failure-signature")

    agent_error = agent_log_sub.add_parser("error")
    agent_error.add_argument("--session-id", required=True)
    agent_error.add_argument("--agent-name", required=True)
    agent_error.add_argument("--task-id", required=True)
    agent_error.add_argument("--stage", required=True)
    agent_error.add_argument("--message", required=True)
    agent_error.add_argument("--error-type")

    ci_failure_parser = subparsers.add_parser("ci-failure", help="CI failure logging")
    ci_failure_parser.add_argument("--pipeline-id", required=True)
    ci_failure_parser.add_argument("--run-type", required=True)
    ci_failure_parser.add_argument("--gate-id", required=True)
    ci_failure_parser.add_argument("--gate-name", required=True)
    ci_failure_parser.add_argument("--status", required=True)
    ci_failure_parser.add_argument("--duration", type=float, required=True)
    ci_failure_parser.add_argument("--signature", required=True)
    ci_failure_parser.add_argument("--branch")
    ci_failure_parser.add_argument("--pr-id")
    ci_failure_parser.add_argument("--commit")
    ci_failure_parser.add_argument("--log-excerpt")
    ci_failure_parser.add_argument("--task-id")

    prod_incident_parser = subparsers.add_parser("prod-incident", help="Prod incident logging")
    prod_incident_parser.add_argument("--env", required=True)
    prod_incident_parser.add_argument("--version", required=True)
    prod_incident_parser.add_argument("--incident-id", required=True)
    prod_incident_parser.add_argument("--severity", required=True)
    prod_incident_parser.add_argument("--symptom", required=True)
    prod_incident_parser.add_argument("--signal")
    prod_incident_parser.add_argument("--rollback")

    scan_parser = subparsers.add_parser("scan", help="Scan logs and generate gate improvement issues")
    scan_parser.add_argument("--days", type=int, default=7, help="Days to look back")
    scan_parser.add_argument("--output-dir", help="Output directory for issues")

    rule_improvement_parser = subparsers.add_parser("rule-improvement", help="Rule improvement commands")
    rule_improvement_sub = rule_improvement_parser.add_subparsers(dest="action", required=True)

    rule_evaluate = rule_improvement_sub.add_parser("evaluate", help="Evaluate all rules")
    rule_evaluate.add_argument("--patterns-dir", default="tools/loop_logging/patterns", help="Patterns directory")
    rule_evaluate.add_argument("--thresholds-file", default="tools/loop_logging/thresholds.yaml", help="Thresholds file")
    rule_evaluate.add_argument("--golden-cases-dir", default="tools/loop_logging/golden_cases", help="Golden cases directory")
    rule_evaluate.add_argument("--feedback-dir", default=".trae/loop-log/feedback", help="Feedback directory")

    rule_generate = rule_improvement_sub.add_parser("generate", help="Generate rule improvement issues")
    rule_generate.add_argument("--patterns-dir", default="tools/loop_logging/patterns", help="Patterns directory")
    rule_generate.add_argument("--thresholds-file", default="tools/loop_logging/thresholds.yaml", help="Thresholds file")
    rule_generate.add_argument("--golden-cases-dir", default="tools/loop_logging/golden_cases", help="Golden cases directory")
    rule_generate.add_argument("--feedback-dir", default=".trae/loop-log/feedback", help="Feedback directory")
    rule_generate.add_argument("--output-dir", default=".trae/loop-log", help="Output directory for issues")

    args = parser.parse_args()

    if args.command == "agent-log":
        cmd_agent_log(args)
    elif args.command == "ci-failure":
        cmd_ci_failure(args)
    elif args.command == "prod-incident":
        cmd_prod_incident(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "rule-improvement":
        cmd_rule_improvement(args)

    return 0


def cmd_rule_improvement(args: argparse.Namespace) -> None:
    thresholds = ThresholdManager(args.thresholds_file)
    golden_case_manager = GoldenCaseManager(args.golden_cases_dir)
    feedback_collector = IssueFeedbackCollector(args.feedback_dir)

    threshold_config = thresholds.get_all_thresholds()

    if args.action == "evaluate":
        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, threshold_config["rule_improvement"])
        evaluations = evaluator.evaluate_all_rules()

        if not evaluations:
            print("No rules with feedback data found")
            return

        print(f"Evaluated {len(evaluations)} rules:")
        for eval_result in evaluations:
            print(f"\nRule: {eval_result.rule_name} ({eval_result.rule_id})")
            print(f"  Total Issues: {eval_result.total_issues}")
            print(f"  Accepted: {eval_result.accepted_issues}")
            print(f"  Rejected: {eval_result.rejected_issues}")
            print(f"  Adoption Rate: {eval_result.adoption_rate:.2f}")
            print(f"  False Positive Rate: {eval_result.false_positive_rate:.2f}")
            print(f"  False Negative Count: {eval_result.false_negative_count}")
            print(f"  Needs Improvement: {eval_result.needs_improvement}")
            if eval_result.improvement_reasons:
                print("  Reasons:")
                for reason in eval_result.improvement_reasons:
                    print(f"    - {reason}")

    elif args.action == "generate":
        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, threshold_config["rule_improvement"])
        evaluations = evaluator.evaluate_all_rules()

        generator = RuleImprovementGenerator()
        issues = generator.generate_all_improvement_issues(evaluations, threshold_config["rule_improvement"])

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"rule_improvement_issues_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

        with open(output_file, "w", encoding="utf-8") as f:
            for issue in issues:
                issue_dict = {
                    "ts": issue.ts.isoformat(),
                    "issue_id": issue.issue_id,
                    "issue_type": issue.issue_type,
                    "rule_id": issue.rule_id,
                    "rule_name": issue.rule_name,
                    "change_type": issue.change_type,
                    "priority": issue.priority,
                    "context": issue.context,
                    "observed_drift": issue.observed_drift,
                    "proposed_change": issue.proposed_change,
                    "acceptance": issue.acceptance,
                    "validation_data": issue.validation_data,
                    "risk": issue.risk,
                }
                f.write(json.dumps(issue_dict) + "\n")

        print(f"Generated {len(issues)} rule improvement issues")
        print(f"Issues written to: {output_file}")

        for issue in issues[:5]:
            print(f"\nPriority: {issue.priority}")
            print(f"Rule: {issue.rule_name}")
            print(f"Change Type: {issue.change_type}")
            print(f"Context: {json.dumps(issue.context, indent=2)}")


if __name__ == "__main__":
    sys.exit(main())