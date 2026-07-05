from __future__ import annotations

import os
import tempfile
import pytest

from ..rule_registry import RuleRegistry, PatternRule


def test_rule_registry_load_rules():
    with tempfile.TemporaryDirectory() as tmpdir:
        rule_file = os.path.join(tmpdir, "test_rule.yaml")
        with open(rule_file, "w") as f:
            f.write("""rules:
  - rule_id: "test_rule"
    rule_name: "Test Rule"
    gap_type: "missing_gate"
    description: "Test rule description"
    match_patterns:
      - "error"
    exclude_patterns:
      - "warning"
    confidence_threshold: 0.8
    priority: "p1"
    version: "1.0.0"
""")

        registry = RuleRegistry(tmpdir)
        assert registry.get_rule_count() == 1
        rule = registry.get_rule("test_rule")
        assert rule is not None
        assert rule.rule_name == "Test Rule"
        assert rule.gap_type == "missing_gate"
        assert rule.confidence_threshold == 0.8


def test_rule_registry_get_rules_by_gap_type():
    with tempfile.TemporaryDirectory() as tmpdir:
        rule_file = os.path.join(tmpdir, "test_rules.yaml")
        with open(rule_file, "w") as f:
            f.write("""rules:
  - rule_id: "rule1"
    rule_name: "Rule 1"
    gap_type: "missing_gate"
    description: "Rule 1"
  - rule_id: "rule2"
    rule_name: "Rule 2"
    gap_type: "coverage_gap"
    description: "Rule 2"
  - rule_id: "rule3"
    rule_name: "Rule 3"
    gap_type: "missing_gate"
    description: "Rule 3"
""")

        registry = RuleRegistry(tmpdir)
        missing_gate_rules = registry.get_rules_by_gap_type("missing_gate")
        assert len(missing_gate_rules) == 2


def test_rule_registry_add_and_remove_rule():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = RuleRegistry(tmpdir)

        new_rule = PatternRule(
            rule_id="new_rule",
            rule_name="New Rule",
            gap_type="gate_noise",
            description="New rule",
        )
        registry.add_rule(new_rule)
        assert registry.get_rule_count() == 1
        assert registry.get_rule("new_rule") is not None

        assert registry.remove_rule("new_rule") is True
        assert registry.get_rule_count() == 0
        assert registry.get_rule("new_rule") is None


def test_rule_registry_empty_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = RuleRegistry(tmpdir)
        assert registry.get_rule_count() == 0
        assert registry.list_all_rules() == []