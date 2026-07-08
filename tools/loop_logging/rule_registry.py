from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PatternRule:
    rule_id: str
    rule_name: str
    gap_type: str
    description: str
    match_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    priority: str = "p1"
    version: str = "1.0.0"


class RuleRegistry:
    def __init__(self, patterns_dir: str) -> None:
        self.patterns_dir: str = patterns_dir
        self.rules: Dict[str, PatternRule] = {}
        self._load_rules()

    def _load_rules(self) -> None:
        if not os.path.exists(self.patterns_dir):
            return

        for filename in os.listdir(self.patterns_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.patterns_dir, filename)
                self._load_rule_file(filepath)

    def _load_rule_file(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict) and "rules" in data:
            for rule_data in data["rules"]:
                rule = PatternRule(
                    rule_id=rule_data["rule_id"],
                    rule_name=rule_data["rule_name"],
                    gap_type=rule_data["gap_type"],
                    description=rule_data["description"],
                    match_patterns=rule_data.get("match_patterns", []),
                    exclude_patterns=rule_data.get("exclude_patterns", []),
                    confidence_threshold=rule_data.get("confidence_threshold", 0.7),
                    priority=rule_data.get("priority", "p1"),
                    version=rule_data.get("version", "1.0.0"),
                )
                self.rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> Optional[PatternRule]:
        return self.rules.get(rule_id)

    def get_rules_by_gap_type(self, gap_type: str) -> List[PatternRule]:
        return [rule for rule in self.rules.values() if rule.gap_type == gap_type]

    def list_all_rules(self) -> List[PatternRule]:
        return list(self.rules.values())

    def add_rule(self, rule: PatternRule) -> None:
        self.rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def save_rule(self, rule: PatternRule) -> None:
        filepath = os.path.join(self.patterns_dir, f"{rule.rule_id}.yaml")
        data = {
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "gap_type": rule.gap_type,
                    "description": rule.description,
                    "match_patterns": rule.match_patterns,
                    "exclude_patterns": rule.exclude_patterns,
                    "confidence_threshold": rule.confidence_threshold,
                    "priority": rule.priority,
                    "version": rule.version,
                }
            ]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_rule_count(self) -> int:
        return len(self.rules)