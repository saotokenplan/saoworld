from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .schema import CIFailureLogEntry, CIStatus, CITriggerType, GapType


class CIFailureLogger:
    def __init__(self, log_dir: Optional[str] = None) -> None:
        self.log_dir: Path = Path(log_dir or ".trae/loop-log")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"ci_failures_{today}.jsonl"

    def log(
        self,
        pipeline_id: str,
        run_type: CITriggerType | str,
        gate_id: str,
        gate_name: str,
        status: CIStatus | str,
        duration_s: float,
        failure_signature: str,
        ts: Optional[datetime] = None,
        branch: Optional[str] = None,
        pr_id: Optional[str] = None,
        commit: Optional[str] = None,
        log_excerpt: Optional[str] = None,
        suspected_category: Optional[GapType | str] = None,
        related_task_id: Optional[str] = None,
    ) -> None:
        if isinstance(run_type, str):
            run_type = CITriggerType(run_type)
        if isinstance(status, str):
            status = CIStatus(status)
        if isinstance(suspected_category, str):
            suspected_category = GapType(suspected_category)

        entry = CIFailureLogEntry(
            pipeline_id=pipeline_id,
            run_type=run_type,
            gate_id=gate_id,
            gate_name=gate_name,
            status=status,
            duration_s=duration_s,
            failure_signature=failure_signature,
            ts=ts,
            branch=branch,
            pr_id=pr_id,
            commit=commit,
            log_excerpt=log_excerpt,
            suspected_category=suspected_category,
            related_task_id=related_task_id,
        )

        log_path = self._get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def read_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        gate_id: Optional[str] = None,
        failure_signature: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        logs: list[dict[str, Any]] = []

        for log_file in self.log_dir.glob("ci_failures_*.jsonl"):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_ts = datetime.fromisoformat(entry["ts"])

                        if start_time and entry_ts < start_time:
                            continue
                        if end_time and entry_ts > end_time:
                            continue
                        if gate_id and entry["gate_id"] != gate_id:
                            continue
                        if failure_signature and failure_signature not in entry["failure_signature"]:
                            continue

                        logs.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue

        return sorted(logs, key=lambda x: x["ts"])