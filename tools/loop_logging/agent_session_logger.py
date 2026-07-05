from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .schema import AgentSessionLogEntry, AgentSessionStage, AgentSessionEvent


class AgentSessionLogger:
    def __init__(self, log_dir: Optional[str] = None) -> None:
        self.log_dir: Path = Path(log_dir or ".trae/loop-log")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_session_id: Optional[str] = None

    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id

    @current_session_id.setter
    def current_session_id(self, session_id: str) -> None:
        self._current_session_id = session_id

    def _get_log_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"agent_session_log_{today}.jsonl"

    def log(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        stage: AgentSessionStage | str,
        event: AgentSessionEvent | str,
        ts: Optional[datetime] = None,
        repo: Optional[str] = None,
        summary: Optional[str] = None,
        artifacts: Optional[dict[str, Any]] = None,
        signals: Optional[dict[str, Any]] = None,
        error: Optional[dict[str, Any]] = None,
    ) -> None:
        if isinstance(stage, str):
            stage = AgentSessionStage(stage)
        if isinstance(event, str):
            event = AgentSessionEvent(event)

        entry = AgentSessionLogEntry(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=stage,
            event=event,
            ts=ts,
            repo=repo,
            summary=summary,
            artifacts=artifacts,
            signals=signals,
            error=error,
        )

        log_path = self._get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def log_start(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        stage: AgentSessionStage | str = AgentSessionStage.PLAN,
        summary: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> None:
        self._current_session_id = session_id
        self.log(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=stage,
            event=AgentSessionEvent.START,
            summary=summary,
            repo=repo,
        )

    def log_end(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        stage: AgentSessionStage | str,
        summary: Optional[str] = None,
        artifacts: Optional[dict[str, Any]] = None,
        signals: Optional[dict[str, Any]] = None,
    ) -> None:
        self.log(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=stage,
            event=AgentSessionEvent.END,
            summary=summary,
            artifacts=artifacts,
            signals=signals,
        )

    def log_tool_call(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        tool_name: str,
        tool_args: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None,
    ) -> None:
        signals = {
            "tool_name": tool_name,
            "tool_args": tool_args or {},
        }
        if result is not None:
            signals["result"] = result

        self.log(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=AgentSessionStage.IMPLEMENT,
            event=AgentSessionEvent.TOOL_CALL,
            summary=f"Tool call: {tool_name}",
            signals=signals,
        )

    def log_ci_result(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        gate_id: str,
        gate_name: str,
        status: str,
        duration_s: float,
        failure_signature: Optional[str] = None,
    ) -> None:
        signals = {
            "gate_id": gate_id,
            "gate_name": gate_name,
            "status": status,
            "duration_s": duration_s,
        }
        if failure_signature:
            signals["failure_signature"] = failure_signature

        self.log(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=AgentSessionStage.TEST,
            event=AgentSessionEvent.CI_RESULT,
            summary=f"CI result: {gate_name} - {status}",
            signals=signals,
        )

    def log_error(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        stage: AgentSessionStage | str,
        error_message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        error_info = {
            "message": error_message,
        }
        if error_type:
            error_info["type"] = error_type
        if stack_trace:
            error_info["stack_trace"] = stack_trace

        self.log(
            session_id=session_id,
            agent_name=agent_name,
            task_id=task_id,
            stage=stage,
            event=AgentSessionEvent.ERROR,
            summary=f"Error: {error_message}",
            error=error_info,
        )

    def read_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        logs: list[dict[str, Any]] = []

        for log_file in self.log_dir.glob("agent_session_log_*.jsonl"):
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
                        if session_id and entry["session_id"] != session_id:
                            continue
                        if task_id and entry["task_id"] != task_id:
                            continue

                        logs.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue

        return sorted(logs, key=lambda x: x["ts"])