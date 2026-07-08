from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class IssueFeedback:
    issue_id: str
    rule_id: str
    issue_type: str
    status: str
    ts: datetime = field(default_factory=datetime.now)
    acceptance: Optional[str] = None
    comments: List[str] = field(default_factory=list)
    improvement_effect: Optional[float] = None
    improvement_cost_hours: Optional[float] = None
    related_prs: List[str] = field(default_factory=list)


class IssueFeedbackCollector:
    def __init__(self, feedback_dir: str) -> None:
        self.feedback_dir: str = feedback_dir
        self.feedbacks: Dict[str, IssueFeedback] = {}
        self._load_feedbacks()

    def _load_feedbacks(self) -> None:
        if not os.path.exists(self.feedback_dir):
            return

        for filename in os.listdir(self.feedback_dir):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(self.feedback_dir, filename)
                self._load_feedback_file(filepath)

    def _load_feedback_file(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        feedback = IssueFeedback(
                            issue_id=data["issue_id"],
                            rule_id=data["rule_id"],
                            issue_type=data["issue_type"],
                            status=data["status"],
                            ts=datetime.fromisoformat(data.get("ts", datetime.now().isoformat())),
                            acceptance=data.get("acceptance"),
                            comments=data.get("comments", []),
                            improvement_effect=data.get("improvement_effect"),
                            improvement_cost_hours=data.get("improvement_cost_hours"),
                            related_prs=data.get("related_prs", []),
                        )
                        self.feedbacks[feedback.issue_id] = feedback
                    except (json.JSONDecodeError, KeyError):
                        continue

    def add_feedback(self, feedback: IssueFeedback) -> None:
        self.feedbacks[feedback.issue_id] = feedback

    def get_feedback(self, issue_id: str) -> Optional[IssueFeedback]:
        return self.feedbacks.get(issue_id)

    def get_feedbacks_by_rule_id(self, rule_id: str) -> List[IssueFeedback]:
        return [fb for fb in self.feedbacks.values() if fb.rule_id == rule_id]

    def get_accepted_feedbacks(self) -> List[IssueFeedback]:
        return [fb for fb in self.feedbacks.values() if fb.acceptance == "accepted"]

    def get_rejected_feedbacks(self) -> List[IssueFeedback]:
        return [fb for fb in self.feedbacks.values() if fb.acceptance == "rejected"]

    def get_pending_feedbacks(self) -> List[IssueFeedback]:
        return [fb for fb in self.feedbacks.values() if fb.acceptance is None]

    def save_feedbacks(self) -> None:
        os.makedirs(self.feedback_dir, exist_ok=True)
        filepath = os.path.join(self.feedback_dir, "issue_feedback.jsonl")
        with open(filepath, "w", encoding="utf-8") as f:
            for feedback in self.feedbacks.values():
                fb_dict = {
                    "issue_id": feedback.issue_id,
                    "rule_id": feedback.rule_id,
                    "issue_type": feedback.issue_type,
                    "status": feedback.status,
                    "ts": feedback.ts.isoformat(),
                    "acceptance": feedback.acceptance,
                    "comments": feedback.comments,
                    "improvement_effect": feedback.improvement_effect,
                    "improvement_cost_hours": feedback.improvement_cost_hours,
                    "related_prs": feedback.related_prs,
                }
                f.write(json.dumps(fb_dict) + "\n")

    def get_feedback_count(self) -> int:
        return len(self.feedbacks)