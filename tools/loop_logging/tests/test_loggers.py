from __future__ import annotations

import json
import os
import tempfile


from ..agent_session_logger import AgentSessionLogger
from ..ci_failure_logger import CIFailureLogger
from ..prod_incident_logger import ProdIncidentLogger


class TestAgentSessionLogger:
    def test_log_start(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AgentSessionLogger(tmpdir)
            logger.log_start("S-001", "TestAgent", "TASK-001", "plan", "Test session")

            log_files = [f for f in os.listdir(tmpdir) if f.startswith("agent_session_log")]
            assert len(log_files) == 1

            with open(os.path.join(tmpdir, log_files[0]), "r") as f:
                lines = f.readlines()
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert entry["session_id"] == "S-001"
                assert entry["agent_name"] == "TestAgent"
                assert entry["task_id"] == "TASK-001"
                assert entry["stage"] == "plan"
                assert entry["event"] == "start"

    def test_log_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AgentSessionLogger(tmpdir)
            logger.log_end("S-001", "TestAgent", "TASK-001", "implement", "Done")

            log_files = [f for f in os.listdir(tmpdir) if f.startswith("agent_session_log")]
            assert len(log_files) == 1

            with open(os.path.join(tmpdir, log_files[0]), "r") as f:
                lines = f.readlines()
                entry = json.loads(lines[0])
                assert entry["event"] == "end"
                assert entry["stage"] == "implement"

    def test_log_ci_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AgentSessionLogger(tmpdir)
            logger.log_ci_result("S-001", "TestAgent", "TASK-001", "G-UNIT-001", "Unit Tests", "failed", 45.0, "TS2322")

            log_files = [f for f in os.listdir(tmpdir) if f.startswith("agent_session_log")]
            with open(os.path.join(tmpdir, log_files[0]), "r") as f:
                lines = f.readlines()
                entry = json.loads(lines[0])
                assert entry["event"] == "ci_result"
                assert entry["signals"]["gate_id"] == "G-UNIT-001"
                assert entry["signals"]["failure_signature"] == "TS2322"

    def test_read_logs_filter_by_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AgentSessionLogger(tmpdir)
            logger.log_start("S-001", "TestAgent", "TASK-001")
            logger.log_start("S-002", "TestAgent", "TASK-002")

            logs = logger.read_logs(session_id="S-001")
            assert len(logs) == 1
            assert logs[0]["session_id"] == "S-001"


class TestCIFailureLogger:
    def test_log_ci_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CIFailureLogger(tmpdir)
            logger.log(
                pipeline_id="CI-001",
                run_type="on_pr",
                gate_id="G-UNIT-001",
                gate_name="Unit Tests",
                status="failed",
                duration_s=60.0,
                failure_signature="AssertionError",
                branch="feature/test",
            )

            log_files = [f for f in os.listdir(tmpdir) if f.startswith("ci_failures")]
            assert len(log_files) == 1

            with open(os.path.join(tmpdir, log_files[0]), "r") as f:
                lines = f.readlines()
                entry = json.loads(lines[0])
                assert entry["pipeline_id"] == "CI-001"
                assert entry["gate_id"] == "G-UNIT-001"
                assert entry["failure_signature"] == "AssertionError"

    def test_read_logs_filter_by_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = CIFailureLogger(tmpdir)
            logger.log(
                pipeline_id="CI-001",
                run_type="on_pr",
                gate_id="G-UNIT-001",
                gate_name="Unit Tests",
                status="failed",
                duration_s=60.0,
                failure_signature="Error1",
            )
            logger.log(
                pipeline_id="CI-002",
                run_type="on_pr",
                gate_id="G-UNIT-002",
                gate_name="Integration Tests",
                status="failed",
                duration_s=120.0,
                failure_signature="Error2",
            )

            logs = logger.read_logs(gate_id="G-UNIT-001")
            assert len(logs) == 1
            assert logs[0]["gate_id"] == "G-UNIT-001"


class TestProdIncidentLogger:
    def test_log_prod_incident(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProdIncidentLogger(tmpdir)
            logger.log(
                env="prod",
                version="v1.0.0",
                incident_id="INC-001",
                severity="sev2",
                symptom="High error rate",
                signal={"metric": "error_rate", "value": 0.15},
            )

            log_files = [f for f in os.listdir(tmpdir) if f.startswith("prod_incidents")]
            assert len(log_files) == 1

            with open(os.path.join(tmpdir, log_files[0]), "r") as f:
                lines = f.readlines()
                entry = json.loads(lines[0])
                assert entry["incident_id"] == "INC-001"
                assert entry["env"] == "prod"
                assert entry["severity"] == "sev2"
                assert entry["signal"]["metric"] == "error_rate"

    def test_read_logs_filter_by_severity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProdIncidentLogger(tmpdir)
            logger.log(env="prod", version="v1.0.0", incident_id="INC-001", severity="sev1", symptom="Critical issue")
            logger.log(env="prod", version="v1.0.0", incident_id="INC-002", severity="sev3", symptom="Minor issue")

            logs = logger.read_logs(severity="sev1")
            assert len(logs) == 1
            assert logs[0]["severity"] == "sev1"
