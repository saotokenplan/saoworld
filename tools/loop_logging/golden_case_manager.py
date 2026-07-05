from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class GoldenCase:
    case_id: str
    case_type: str
    gap_type: str
    rule_id: str
    failure_signature: str
    description: str
    expected_outcome: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class GoldenCaseManager:
    def __init__(self, golden_cases_dir: str) -> None:
        self.golden_cases_dir: str = golden_cases_dir
        self.cases: Dict[str, GoldenCase] = {}
        self._load_cases()

    def _load_cases(self) -> None:
        if not os.path.exists(self.golden_cases_dir):
            return

        for filename in os.listdir(self.golden_cases_dir):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(self.golden_cases_dir, filename)
                self._load_case_file(filepath)

    def _load_case_file(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        case = GoldenCase(
                            case_id=data["case_id"],
                            case_type=data["case_type"],
                            gap_type=data["gap_type"],
                            rule_id=data["rule_id"],
                            failure_signature=data["failure_signature"],
                            description=data["description"],
                            expected_outcome=data["expected_outcome"],
                            evidence=data.get("evidence", {}),
                            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                        )
                        self.cases[case.case_id] = case
                    except (json.JSONDecodeError, KeyError) as e:
                        continue

    def add_case(self, case: GoldenCase) -> None:
        self.cases[case.case_id] = case

    def get_case(self, case_id: str) -> Optional[GoldenCase]:
        return self.cases.get(case_id)

    def get_cases_by_rule_id(self, rule_id: str) -> List[GoldenCase]:
        return [case for case in self.cases.values() if case.rule_id == rule_id]

    def get_cases_by_gap_type(self, gap_type: str) -> List[GoldenCase]:
        return [case for case in self.cases.values() if case.gap_type == gap_type]

    def get_positive_cases(self) -> List[GoldenCase]:
        return [case for case in self.cases.values() if case.case_type == "positive"]

    def get_negative_cases(self) -> List[GoldenCase]:
        return [case for case in self.cases.values() if case.case_type == "negative"]

    def remove_case(self, case_id: str) -> bool:
        if case_id in self.cases:
            del self.cases[case_id]
            return True
        return False

    def save_cases(self) -> None:
        os.makedirs(self.golden_cases_dir, exist_ok=True)
        cases_by_gap = {}
        for case in self.cases.values():
            if case.gap_type not in cases_by_gap:
                cases_by_gap[case.gap_type] = []
            cases_by_gap[case.gap_type].append(case)

        for gap_type, gap_cases in cases_by_gap.items():
            filename = f"{gap_type}_cases.jsonl"
            filepath = os.path.join(self.golden_cases_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                for case in gap_cases:
                    case_dict = {
                        "case_id": case.case_id,
                        "case_type": case.case_type,
                        "gap_type": case.gap_type,
                        "rule_id": case.rule_id,
                        "failure_signature": case.failure_signature,
                        "description": case.description,
                        "expected_outcome": case.expected_outcome,
                        "evidence": case.evidence,
                        "created_at": case.created_at.isoformat(),
                        "updated_at": case.updated_at.isoformat(),
                    }
                    f.write(json.dumps(case_dict) + "\n")

    def get_case_count(self) -> int:
        return len(self.cases)