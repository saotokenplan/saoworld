from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any


class AgentSessionStage(str, Enum):
    PLAN = "plan"
    IMPLEMENT = "implement"
    TEST = "test"
    FIX = "fix"
    RELEASE = "release"


class AgentSessionEvent(str, Enum):
    START = "start"
    END = "end"
    TOOL_CALL = "tool_call"
    CI_RESULT = "ci_result"
    ERROR = "error"


class CIStatus(str, Enum):
    FAILED = "failed"
    FLAKY = "flaky"
    TIMEOUT = "timeout"


class CITriggerType(str, Enum):
    ON_PR = "on_pr"
    NIGHTLY = "nightly"
    MANUAL = "manual"


class IncidentEnvironment(str, Enum):
    PROD = "prod"
    STAGING = "staging"
    GRAY = "gray"


class IncidentSeverity(str, Enum):
    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"


class GapType(str, Enum):
    MISSING_GATE = "missing_gate"
    COVERAGE_GAP = "coverage_gap"
    GATE_NOISE = "gate_noise"


class GateType(str, Enum):
    STATIC = "static"
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    NONFUNCTIONAL = "nonfunctional"
    CONTENT = "content"


class GateSeverity(str, Enum):
    BLOCKER = "blocker"
    WARN = "warn"


class GateTrigger(str, Enum):
    ON_PR = "on_pr"
    NIGHTLY = "nightly"
    MANUAL = "manual"


class AgentSessionLogEntry:
    def __init__(
        self,
        session_id: str,
        agent_name: str,
        task_id: str,
        stage: AgentSessionStage,
        event: AgentSessionEvent,
        ts: Optional[datetime] = None,
        repo: Optional[str] = None,
        summary: Optional[str] = None,
        artifacts: Optional[dict[str, Any]] = None,
        signals: Optional[dict[str, Any]] = None,
        error: Optional[dict[str, Any]] = None,
    ) -> None:
        self.ts: datetime = ts or datetime.now()
        self.session_id: str = session_id
        self.agent_name: str = agent_name
        self.repo: Optional[str] = repo
        self.task_id: str = task_id
        self.stage: AgentSessionStage = stage
        self.event: AgentSessionEvent = event
        self.summary: Optional[str] = summary
        self.artifacts: dict[str, Any] = artifacts or {}
        self.signals: dict[str, Any] = signals or {}
        self.error: Optional[dict[str, Any]] = error

    def to_dict(self) -> dict[str, Any]:
        result = {
            "ts": self.ts.isoformat(),
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "stage": self.stage.value,
            "event": self.event.value,
        }
        if self.repo:
            result["repo"] = self.repo
        if self.summary:
            result["summary"] = self.summary
        if self.artifacts:
            result["artifacts"] = self.artifacts
        if self.signals:
            result["signals"] = self.signals
        if self.error:
            result["error"] = self.error
        return result


class CIFailureLogEntry:
    def __init__(
        self,
        pipeline_id: str,
        run_type: CITriggerType,
        gate_id: str,
        gate_name: str,
        status: CIStatus,
        duration_s: float,
        failure_signature: str,
        ts: Optional[datetime] = None,
        branch: Optional[str] = None,
        pr_id: Optional[str] = None,
        commit: Optional[str] = None,
        log_excerpt: Optional[str] = None,
        suspected_category: Optional[GapType] = None,
        related_task_id: Optional[str] = None,
    ) -> None:
        self.ts: datetime = ts or datetime.now()
        self.pipeline_id: str = pipeline_id
        self.run_type: CITriggerType = run_type
        self.branch: Optional[str] = branch
        self.pr_id: Optional[str] = pr_id
        self.commit: Optional[str] = commit
        self.gate_id: str = gate_id
        self.gate_name: str = gate_name
        self.status: CIStatus = status
        self.duration_s: float = duration_s
        self.failure_signature: str = failure_signature
        self.log_excerpt: Optional[str] = log_excerpt
        self.suspected_category: Optional[GapType] = suspected_category
        self.related_task_id: Optional[str] = related_task_id

    def to_dict(self) -> dict[str, Any]:
        result = {
            "ts": self.ts.isoformat(),
            "pipeline_id": self.pipeline_id,
            "run_type": self.run_type.value,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "status": self.status.value,
            "duration_s": self.duration_s,
            "failure_signature": self.failure_signature,
        }
        if self.branch:
            result["branch"] = self.branch
        if self.pr_id:
            result["pr_id"] = self.pr_id
        if self.commit:
            result["commit"] = self.commit
        if self.log_excerpt:
            result["log_excerpt"] = log_excerpt
        if self.suspected_category:
            result["suspected_category"] = self.suspected_category.value
        if self.related_task_id:
            result["related_task_id"] = self.related_task_id
        return result


class ProdIncidentLogEntry:
    def __init__(
        self,
        env: IncidentEnvironment,
        version: str,
        incident_id: str,
        severity: IncidentSeverity,
        symptom: str,
        ts: Optional[datetime] = None,
        signal: Optional[dict[str, Any]] = None,
        suspected_gate_gap: Optional[dict[str, Any]] = None,
        rollback: Optional[dict[str, Any]] = None,
        links: Optional[dict[str, Any]] = None,
    ) -> None:
        self.ts: datetime = ts or datetime.now()
        self.env: IncidentEnvironment = env
        self.version: str = version
        self.incident_id: str = incident_id
        self.severity: IncidentSeverity = severity
        self.symptom: str = symptom
        self.signal: dict[str, Any] = signal or {}
        self.suspected_gate_gap: dict[str, Any] = suspected_gate_gap or {}
        self.rollback: dict[str, Any] = rollback or {}
        self.links: dict[str, Any] = links or {}

    def to_dict(self) -> dict[str, Any]:
        result = {
            "ts": self.ts.isoformat(),
            "env": self.env.value,
            "version": self.version,
            "incident_id": self.incident_id,
            "severity": self.severity.value,
            "symptom": self.symptom,
        }
        if self.signal:
            result["signal"] = self.signal
        if self.suspected_gate_gap:
            result["suspected_gate_gap"] = self.suspected_gate_gap
        if self.rollback:
            result["rollback"] = self.rollback
        if self.links:
            result["links"] = self.links
        return result


class GateImprovementIssue:
    def __init__(
        self,
        symptom: str,
        root_cause_hypothesis: str,
        gap_type: GapType,
        gate_type: GateType,
        gate_name: str,
        trigger_strategy: GateTrigger,
        command: str,
        risk_coverage: list[str],
        acceptance: list[str],
        ts: Optional[datetime] = None,
        priority: str = "p1",
        evidence: Optional[list[dict[str, Any]]] = None,
        expected_seconds: float = 60.0,
        flakiness_budget: float = 0.005,
        severity: GateSeverity = GateSeverity.BLOCKER,
    ) -> None:
        self.ts: datetime = ts or datetime.now()
        self.issue_type: str = "gate_improvement"
        self.priority: str = priority
        self.symptom: str = symptom
        self.root_cause_hypothesis: str = root_cause_hypothesis
        self.gap_type: GapType = gap_type
        self.proposed_gate: dict[str, Any] = {
            "type": gate_type.value,
            "name": gate_name,
            "trigger": trigger_strategy.value,
            "command": command,
            "risk_coverage": risk_coverage,
            "expected_seconds": expected_seconds,
            "flakiness_budget": flakiness_budget,
            "severity": severity.value,
        }
        self.acceptance: list[str] = acceptance
        self.evidence: list[dict[str, Any]] = evidence or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts.isoformat(),
            "issue_type": self.issue_type,
            "priority": self.priority,
            "symptom": self.symptom,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "gap_type": self.gap_type.value,
            "proposed_gate": self.proposed_gate,
            "acceptance": self.acceptance,
            "evidence": self.evidence,
        }