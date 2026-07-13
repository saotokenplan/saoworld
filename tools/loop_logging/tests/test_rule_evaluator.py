from __future__ import annotations

import os
import tempfile
import pytest

from ..rule_evaluator import RuleEvaluator
from ..feedback_collector import IssueFeedbackCollector
from ..golden_case_manager import GoldenCaseManager


def test_rule_evaluator_basic_evaluation():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_file = os.path.join(tmpdir, "issue_feedback.jsonl")
        with open(feedback_file, "w") as f:
            f.write(
                '{"issue_id": "ISSUE-001", "rule_id": "test_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-002", "rule_id": "test_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-003", "rule_id": "test_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "rejected"}\n'
            )

        feedback_collector = IssueFeedbackCollector(tmpdir)
        golden_case_manager = GoldenCaseManager(tmpdir)
        thresholds = {
            "min_issue_adoption_rate": 0.6,
            "max_false_positive_rate": 0.35,
            "max_false_negative_rate": 0.2,
            "max_latency_hours": 24,
            "alert_threshold": 0.2,
        }

        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, thresholds)
        result = evaluator.evaluate_rule("test_rule")

        assert result.total_issues == 3
        assert result.accepted_issues == 2
        assert result.rejected_issues == 1
        assert result.adoption_rate == pytest.approx(2/3, 0.01)
        assert result.false_positive_rate == pytest.approx(1/3, 0.01)
        assert not result.needs_improvement


def test_rule_evaluator_needs_improvement_high_false_positive():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_file = os.path.join(tmpdir, "issue_feedback.jsonl")
        with open(feedback_file, "w") as f:
            f.write(
                '{"issue_id": "ISSUE-001", "rule_id": "bad_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-002", "rule_id": "bad_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "rejected"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-003", "rule_id": "bad_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "rejected"}\n'
            )

        feedback_collector = IssueFeedbackCollector(tmpdir)
        golden_case_manager = GoldenCaseManager(tmpdir)
        thresholds = {
            "min_issue_adoption_rate": 0.6,
            "max_false_positive_rate": 0.35,
            "max_false_negative_rate": 0.2,
            "max_latency_hours": 24,
            "alert_threshold": 0.2,
        }

        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, thresholds)
        result = evaluator.evaluate_rule("bad_rule")

        assert result.false_positive_rate > 0.35
        assert result.needs_improvement
        assert any("误报率" in reason for reason in result.improvement_reasons)


def test_rule_evaluator_false_negatives():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_file = os.path.join(tmpdir, "issue_feedback.jsonl")
        with open(feedback_file, "w") as f:
            f.write(
                '{"issue_id": "ISSUE-001", "rule_id": "test_rule", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )

        golden_cases_file = os.path.join(tmpdir, "missing_gate_cases.jsonl")
        with open(golden_cases_file, "w") as f:
            f.write(
                '{"case_id": "case1", "case_type": "positive", '
                '"gap_type": "missing_gate", "rule_id": "test_rule", '
                '"failure_signature": "sig1", "description": "Test", '
                '"expected_outcome": "test"}\n'
            )
            f.write(
                '{"case_id": "case2", "case_type": "positive", '
                '"gap_type": "missing_gate", "rule_id": "test_rule", '
                '"failure_signature": "sig2", "description": "Test", '
                '"expected_outcome": "test"}\n'
            )

        feedback_collector = IssueFeedbackCollector(tmpdir)
        golden_case_manager = GoldenCaseManager(tmpdir)
        thresholds = {
            "min_issue_adoption_rate": 0.6,
            "max_false_positive_rate": 0.35,
            "max_false_negative_rate": 0.2,
            "max_latency_hours": 24,
            "alert_threshold": 0.2,
        }

        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, thresholds)
        result = evaluator.evaluate_rule("test_rule")

        assert result.false_negative_count > 0
        assert result.needs_improvement


def test_rule_evaluator_no_feedback():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_collector = IssueFeedbackCollector(tmpdir)
        golden_case_manager = GoldenCaseManager(tmpdir)
        thresholds = {
            "min_issue_adoption_rate": 0.6,
            "max_false_positive_rate": 0.35,
            "max_false_negative_rate": 0.2,
            "max_latency_hours": 24,
            "alert_threshold": 0.2,
        }

        evaluator = RuleEvaluator(feedback_collector, golden_case_manager, thresholds)
        result = evaluator.evaluate_rule("no_data_rule")

        assert result.total_issues == 0
        assert result.adoption_rate == 0.0
        assert result.false_positive_rate == 0.0
