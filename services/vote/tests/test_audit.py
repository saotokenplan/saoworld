"""审计日志持久化测试。"""

import uuid

from sqlalchemy import select

from app.domain.models import AuditLog
from app.repositories.audit_repo import (
    ACTION_VOTE_CYCLE_CREATE,
    ACTION_VOTE_CYCLE_TRANSITION,
    ACTION_VOTE_SUBMIT,
)


def _sample_candidates() -> list[dict]:
    return [
        {
            "title": "候选A",
            "summary": "候选A摘要",
            "region_scope": ["region_a"],
            "risk_tags": [],
        },
        {
            "title": "候选B",
            "summary": "候选B摘要",
            "region_scope": ["region_b"],
            "risk_tags": [],
        },
    ]


class TestVoteSubmitAuditLog:
    """投票提交时的审计日志测试。"""

    async def test_submit_vote_creates_audit_log(self, client, open_vote_cycle):
        """投票提交成功后应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        candidate_id = str(open_vote_cycle.candidates[0].candidate_id)
        player_id = str(uuid.uuid4())
        idempotency_key = f"test_{uuid.uuid4().hex}"
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"

        resp = await client.post(
            "/api/v1/votes/submit",
            json={
                "candidate_id": candidate_id,
                "weight": 1.0,
                "device_fingerprint_hash": "hash123",
            },
            headers={
                "X-Player-Id": player_id,
                "Idempotency-Key": idempotency_key,
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 201

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_SUBMIT
        assert audit.operator_id == player_id
        assert audit.operator_role == "player"
        assert audit.resource_type == "vote"
        assert audit.resource_id is not None
        assert audit.result_status == 201
        assert audit.request_payload_jsonb is not None
        assert "candidate_id" in audit.request_payload_jsonb

    async def test_submit_vote_audit_log_with_no_trace_id(self, client, open_vote_cycle):
        """投票提交时不传 trace_id，审计日志仍应有自动生成的 trace_id。"""
        from tests.conftest import TestSessionLocal

        candidate_id = str(open_vote_cycle.candidates[0].candidate_id)
        player_id = str(uuid.uuid4())
        idempotency_key = f"test_{uuid.uuid4().hex}"

        resp = await client.post(
            "/api/v1/votes/submit",
            json={
                "candidate_id": candidate_id,
                "weight": 1.0,
                "device_fingerprint_hash": "hash456",
            },
            headers={
                "X-Player-Id": player_id,
                "Idempotency-Key": idempotency_key,
            },
        )
        assert resp.status_code == 201

        # 查询审计日志（应该有自动生成的 trace_id）
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.operator_id == player_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.trace_id.startswith("trace_")


class TestVoteCycleCreateAuditLog:
    """投票周期创建时的审计日志测试。"""

    async def test_create_vote_cycle_creates_audit_log(self, client, ops_token):
        """创建投票周期成功后应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        trace_id = f"trace_create_{uuid.uuid4().hex[:12]}"
        idempotency_key = f"test_{uuid.uuid4().hex}"

        resp = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "ch_test_audit",
                "starts_at": "2026-07-10T00:00:00Z",
                "ends_at": "2026-07-17T00:00:00Z",
                "reason": "审计日志测试",
                "candidates": _sample_candidates(),
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": idempotency_key,
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 201

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_CYCLE_CREATE
        assert audit.operator_role == "ops"
        assert audit.resource_type == "vote_cycle"
        assert audit.resource_id is not None
        assert audit.reason == "审计日志测试"
        assert audit.result_status == 201
        assert audit.request_payload_jsonb is not None


class TestVoteCycleTransitionAuditLog:
    """投票周期状态迁移时的审计日志测试。"""

    async def _create_cycle(self, client, ops_token, chapter_id: str) -> str:
        """创建投票周期并返回 cycle_id。"""
        idempotency_key = f"test_{uuid.uuid4().hex}"
        resp = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": chapter_id,
                "starts_at": "2026-07-10T00:00:00Z",
                "ends_at": "2026-07-17T00:00:00Z",
                "reason": "审计测试",
                "candidates": _sample_candidates(),
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": idempotency_key,
                "X-Trace-Id": f"trace_create_{chapter_id}",
            },
        )
        assert resp.status_code == 201
        return resp.json()["vote_cycle_id"]

    async def test_schedule_vote_cycle_creates_audit_log(self, client, ops_token):
        """调度投票周期应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        cycle_id = await self._create_cycle(client, ops_token, "ch_audit_schedule")

        trace_id = f"trace_schedule_{uuid.uuid4().hex[:12]}"
        idempotency_key = f"test_{uuid.uuid4().hex}"
        resp = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "调度测试"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": idempotency_key,
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 200

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_CYCLE_TRANSITION
        assert audit.operator_role == "ops"
        assert audit.resource_type == "vote_cycle"
        assert audit.resource_id is not None
        assert audit.reason == "调度测试"
        assert audit.request_payload_jsonb is not None
        assert audit.request_payload_jsonb["from_status"] == "draft"
        assert audit.request_payload_jsonb["to_status"] == "scheduled"

    async def test_open_vote_cycle_creates_audit_log(self, client, ops_token):
        """开放投票周期应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        cycle_id = await self._create_cycle(client, ops_token, "ch_audit_open")

        await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "调度"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": "trace_schedule_open",
            },
        )

        trace_id = f"trace_open_{uuid.uuid4().hex[:12]}"
        resp = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "开放测试"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 200

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_CYCLE_TRANSITION
        assert audit.request_payload_jsonb["from_status"] == "scheduled"
        assert audit.request_payload_jsonb["to_status"] == "open"

    async def test_close_vote_cycle_creates_audit_log(self, client, ops_token):
        """关闭投票周期应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        cycle_id = await self._create_cycle(client, ops_token, "ch_audit_close")

        await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "调度"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": "trace_schedule_close",
            },
        )

        await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "开放"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": "trace_open_close",
            },
        )

        trace_id = f"trace_close_{uuid.uuid4().hex[:12]}"
        resp = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/close",
            json={"reason": "关闭测试"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 200

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_CYCLE_TRANSITION
        assert audit.request_payload_jsonb["from_status"] == "open"
        assert audit.request_payload_jsonb["to_status"] == "closed"

    async def test_finalize_vote_cycle_creates_audit_log(self, client, ops_token):
        """确认投票结果应写入审计日志。"""
        from tests.conftest import TestSessionLocal

        cycle_id = await self._create_cycle(client, ops_token, "ch_audit_finalize")

        for action in ("schedule", "open", "close"):
            await client.post(
                f"/api/v1/ops/vote-cycles/{cycle_id}/{action}",
                json={"reason": action},
                headers={
                    "Authorization": f"Bearer {ops_token}",
                    "Idempotency-Key": f"test_{uuid.uuid4().hex}_{action}",
                    "X-Trace-Id": f"trace_{action}_finalize",
                },
            )

        trace_id = f"trace_finalize_{uuid.uuid4().hex[:12]}"
        resp = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/finalize",
            json={"reason": "确认测试"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"test_{uuid.uuid4().hex}",
                "X-Trace-Id": trace_id,
            },
        )
        assert resp.status_code == 200

        # 查询审计日志
        async with TestSessionLocal() as session:
            stmt = select(AuditLog).where(AuditLog.trace_id == trace_id)
            result = await session.execute(stmt)
            audit = result.scalar_one_or_none()

        assert audit is not None
        assert audit.action == ACTION_VOTE_CYCLE_TRANSITION
        assert audit.request_payload_jsonb["from_status"] == "closed"
        assert audit.request_payload_jsonb["to_status"] == "finalized"
        assert audit.reason == "确认测试"


class TestAuditLogRepository:
    """直接测试 AuditRepository。"""

    async def test_create_audit_log(self, client):
        """直接通过 Repository 写入审计日志。"""
        from tests.conftest import TestSessionLocal
        from app.repositories.audit_repo import AuditRepository, ACTION_VOTE_SUBMIT, RESOURCE_VOTE

        trace_id = f"trace_repo_{uuid.uuid4().hex[:12]}"

        async with TestSessionLocal() as session:
            repo = AuditRepository(session)
            audit = await repo.create_audit_log(
                trace_id=trace_id,
                request_id="req_test_123",
                operator_id="player_001",
                operator_role="player",
                action=ACTION_VOTE_SUBMIT,
                resource_type=RESOURCE_VOTE,
                resource_id=uuid.uuid4(),
                reason=None,
                request_payload_jsonb={"test": True},
                result_status=201,
            )
            await session.commit()

            # 重新查询验证
            stmt = select(AuditLog).where(AuditLog.audit_id == audit.audit_id)
            result = await session.execute(stmt)
            loaded = result.scalar_one()

        assert loaded.trace_id == trace_id
        assert loaded.request_id == "req_test_123"
        assert loaded.operator_id == "player_001"
        assert loaded.operator_role == "player"
        assert loaded.action == ACTION_VOTE_SUBMIT
        assert loaded.resource_type == RESOURCE_VOTE
        assert loaded.request_payload_jsonb == {"test": True}
        assert loaded.result_status == 201
        assert loaded.created_at is not None
