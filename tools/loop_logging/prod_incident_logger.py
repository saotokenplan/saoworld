from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .schema import ProdIncidentLogEntry, IncidentEnvironment, IncidentSeverity


class ProdIncidentLogger:
    def __init__(self, log_dir: Optional[str] = None) -> None:
        self.log_dir: Path = Path(log_dir or ".trae/loop-log")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"prod_incidents_{today}.jsonl"

    def log(
        self,
        env: IncidentEnvironment | str,
        version: str,
        incident_id: str,
        severity: IncidentSeverity | str,
        symptom: str,
        ts: Optional[datetime] = None,
        signal: Optional[dict[str, Any]] = None,
        suspected_gate_gap: Optional[dict[str, Any]] = None,
        rollback: Optional[dict[str, Any]] = None,
        links: Optional[dict[str, Any]] = None,
    ) -> None:
        if isinstance(env, str):
            env = IncidentEnvironment(env)
        if isinstance(severity, str):
            severity = IncidentSeverity(severity)

        entry = ProdIncidentLogEntry(
            env=env,
            version=version,
            incident_id=incident_id,
            severity=severity,
            symptom=symptom,
            ts=ts,
            signal=signal,
            suspected_gate_gap=suspected_gate_gap,
            rollback=rollback,
            links=links,
        )

        log_path = self._get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def read_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        env: Optional[IncidentEnvironment | str] = None,
        severity: Optional[IncidentSeverity | str] = None,
    ) -> list[dict[str, Any]]:
        logs: list[dict[str, Any]] = []

        if isinstance(env, str):
            env = IncidentEnvironment(env)
        if isinstance(severity, str):
            severity = IncidentSeverity(severity)

        for log_file in self.log_dir.glob("prod_incidents_*.jsonl"):
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
                        if env and IncidentEnvironment(entry["env"]) != env:
                            continue
                        if severity and IncidentSeverity(entry["severity"]) != severity:
                            continue

                        logs.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue

        return sorted(logs, key=lambda x: x["ts"])