from __future__ import annotations

from ..issue_generator import GateImprovementIssueGenerator
from ..clusterer import FailureCluster
from ..schema import GapType, GateType, GateTrigger


class TestGateImprovementIssueGenerator:
    def test_generate_issue_for_missing_gate(self) -> None:
        cluster = FailureCluster("TS2322", "mypy")
        cluster.count = 10
        cluster.gate_names = {"Mypy Typecheck"}

        generator = GateImprovementIssueGenerator()
        issue = generator.generate_issue(cluster, GapType.MISSING_GATE)

        assert issue.priority == "p0"
        assert issue.gap_type == GapType.MISSING_GATE
        assert issue.proposed_gate["type"] == "static"
        assert "新增" in issue.proposed_gate["name"]

    def test_generate_issue_for_coverage_gap(self) -> None:
        cluster = FailureCluster("test_vote", "pytest")
        cluster.count = 5
        cluster.gate_names = {"Unit Tests"}

        generator = GateImprovementIssueGenerator()
        issue = generator.generate_issue(cluster, GapType.COVERAGE_GAP)

        assert issue.priority == "p1"
        assert issue.gap_type == GapType.COVERAGE_GAP
        assert issue.proposed_gate["type"] == "unit"
        assert "增强" in issue.proposed_gate["name"]

    def test_generate_issue_for_gate_noise(self) -> None:
        cluster = FailureCluster("flaky_test", "test")
        cluster.count = 3
        cluster.gate_names = {"Integration Tests"}
        cluster.examples = ["test_flaky FAILED (flaky)"]

        generator = GateImprovementIssueGenerator()
        issue = generator.generate_issue(cluster, GapType.GATE_NOISE)

        assert issue.priority == "p2"
        assert issue.gap_type == GapType.GATE_NOISE
        assert "优化" in issue.proposed_gate["name"]

    def test_issue_to_dict(self) -> None:
        cluster = FailureCluster("TS2322", "mypy")
        cluster.count = 5

        generator = GateImprovementIssueGenerator()
        issue = generator.generate_issue(cluster, GapType.MISSING_GATE)

        issue_dict = issue.to_dict()
        assert issue_dict["issue_type"] == "gate_improvement"
        assert issue_dict["priority"] == "p1"
        assert "TS2322" in issue_dict["symptom"]
        assert "proposed_gate" in issue_dict
        assert "acceptance" in issue_dict

    def test_batch_generate_sorts_by_priority(self) -> None:
        cluster_p0 = FailureCluster("TS2322", "mypy")
        cluster_p0.count = 10

        cluster_p1 = FailureCluster("test_a", "pytest")
        cluster_p1.count = 5

        classified_gaps = [
            {"signature": "TS2322", "gap_type": "missing_gate"},
            {"signature": "test_a", "gap_type": "coverage_gap"},
        ]

        generator = GateImprovementIssueGenerator()
        issues = generator.batch_generate(
            classified_gaps,
            {"TS2322": cluster_p0, "test_a": cluster_p1},
        )

        assert len(issues) == 2
        assert issues[0].priority <= issues[1].priority