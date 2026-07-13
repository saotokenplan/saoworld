from __future__ import annotations

import os
import tempfile

from ..feedback_collector import IssueFeedbackCollector, IssueFeedback


def test_feedback_collector_load_feedbacks():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_file = os.path.join(tmpdir, "issue_feedback.jsonl")
        with open(feedback_file, "w") as f:
            f.write(
                '{"issue_id": "ISSUE-001", "rule_id": "rule1", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted", "comments": ["Good issue"], '
                '"improvement_effect": 0.8}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-002", "rule_id": "rule1", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "rejected", "comments": ["Not valid"]}\n'
            )

        collector = IssueFeedbackCollector(tmpdir)
        assert collector.get_feedback_count() == 2
        assert len(collector.get_accepted_feedbacks()) == 1
        assert len(collector.get_rejected_feedbacks()) == 1


def test_feedback_collector_add_and_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        collector = IssueFeedbackCollector(tmpdir)

        feedback = IssueFeedback(
            issue_id="ISSUE-003",
            rule_id="rule2",
            issue_type="gate_improvement",
            status="pending",
        )
        collector.add_feedback(feedback)
        assert collector.get_feedback_count() == 1
        retrieved = collector.get_feedback("ISSUE-003")
        assert retrieved is not None
        assert retrieved.rule_id == "rule2"
        assert retrieved.status == "pending"


def test_feedback_collector_get_by_rule_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback_file = os.path.join(tmpdir, "issue_feedback.jsonl")
        with open(feedback_file, "w") as f:
            f.write(
                '{"issue_id": "ISSUE-001", "rule_id": "rule1", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-002", "rule_id": "rule2", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "accepted"}\n'
            )
            f.write(
                '{"issue_id": "ISSUE-003", "rule_id": "rule1", '
                '"issue_type": "gate_improvement", "status": "completed", '
                '"acceptance": "rejected"}\n'
            )

        collector = IssueFeedbackCollector(tmpdir)
        rule1_feedbacks = collector.get_feedbacks_by_rule_id("rule1")
        assert len(rule1_feedbacks) == 2


def test_feedback_collector_save_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        collector = IssueFeedbackCollector(tmpdir)

        feedback = IssueFeedback(
            issue_id="ISSUE-004",
            rule_id="rule3",
            issue_type="gate_improvement",
            status="completed",
            acceptance="accepted",
        )
        collector.add_feedback(feedback)
        collector.save_feedbacks()

        new_collector = IssueFeedbackCollector(tmpdir)
        assert new_collector.get_feedback_count() == 1
        assert new_collector.get_feedback("ISSUE-004") is not None
