"""WP5 批量生成能力测试（方法级 + 端点级）。

全部基于 MockLLMAdapter + 内存 SQLite，无需真实运行时（PG/Redis/Docker/真实 LLM）。
"""
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.core.content_generator import (
    BatchItemSpec,
    BatchResult,
    ContentGenerator,
    ContentGenerationError,
    SUPPORTED_BATCH_TARGETS,
)
from app.core.errors import GenerationErrorCodes
from app.core.llm_adapter import MockLLMAdapter
from app.core.quality_scorer import QualityScorer
from app.core.template_manager import TemplateManager


@pytest.fixture(autouse=True)
def _lower_quality_threshold(monkeypatch):
    """批量机制测试不关注质量门禁，放宽全局阈值使低质量 mock 通过。"""
    monkeypatch.setattr(settings, "quality_threshold", 0.1)

NPC_MOCK = {
    "npc_key": "npc_test",
    "name": "Test NPC",
    "title": "Test",
    "gender": "male",
    "age": 30,
    "race": "human",
    "faction_key": "faction_ironward",
    "region_key": "region_core",
    "role": "blacksmith",
    "location_key": "loc_test",
    "description": (
        "A skilled blacksmith who has worked in the forge for over 20 years. "
        "He is known for his exceptional craftsmanship and gruff but honest demeanor."
    ),
    "personality": ["gruff", "skilled", "honest"],
    "traits": ["strong", "meticulous"],
    "voice": "deep and gruff",
    "backstory": "Test NPC backstory.",
    "motivation": "To craft the finest weapons and armor.",
    "relationship_map": {},
    "dialog_style": "direct",
    "dialog_nodes": {
        "first_meet": {"id": "first_meet", "text": "Hello!", "speaker": "npc", "choices": []},
        "default": {"id": "default", "text": "Welcome!", "speaker": "npc", "choices": []},
        "goodbye": {"id": "goodbye", "text": "", "speaker": "npc", "choices": [], "is_end": True},
    },
    "quests_given": [],
    "quests_related": [],
    "shop_items": [],
    "services_offered": [],
    "location_x": 100,
    "location_y": 200,
    "interaction_radius": 30,
}


@pytest.fixture
def batch_generator():
    llm_adapter = MockLLMAdapter()
    llm_adapter.mock_response = NPC_MOCK
    return ContentGenerator(
        llm_adapter=llm_adapter,
        template_manager=TemplateManager(),
        quality_scorer=QualityScorer(),
        quality_threshold=0.1,
    )


class TestGenerateBatch:
    """generate_batch 方法级测试（不依赖 HTTP/DB）。"""

    @pytest.mark.asyncio
    async def test_all_success(self, batch_generator):
        specs = [
            BatchItemSpec(target_type="npc", params={"region_id": "r", "chapter_id": "c"})
            for _ in range(3)
        ]
        result = await batch_generator.generate_batch(specs)

        assert isinstance(result, BatchResult)
        assert result.total == 3
        assert result.succeeded == 3
        assert result.failed == 0
        assert all(it.status == "success" and it.data for it in result.items)
        assert all(it.quality_score is not None for it in result.items)

    @pytest.mark.asyncio
    async def test_failure_isolation(self, batch_generator):
        call_count = {"n": 0}

        async def flaky_npc(region_id=None, chapter_id=None, npc_role="commoner", context=None):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise ContentGenerationError("simulated failure")
            return NPC_MOCK

        batch_generator.generate_npc = flaky_npc
        specs = [BatchItemSpec(target_type="npc", params={}) for _ in range(3)]
        result = await batch_generator.generate_batch(specs)

        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1
        failed = [it for it in result.items if it.status == "failed"][0]
        assert "simulated failure" in failed.error

    @pytest.mark.asyncio
    async def test_invalid_target_type_isolated(self, batch_generator):
        specs = [
            BatchItemSpec(target_type="npc", params={}),
            BatchItemSpec(target_type="unknown", params={}),
        ]
        result = await batch_generator.generate_batch(specs)

        assert result.succeeded == 1
        assert result.failed == 1
        assert result.items[1].status == "failed"
        assert "不支持的 target_type" in result.items[1].error

    @pytest.mark.asyncio
    async def test_empty_specs(self, batch_generator):
        result = await batch_generator.generate_batch([])
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_max_items_cap(self, batch_generator, monkeypatch):
        monkeypatch.setattr("app.core.content_generator.settings.batch_max_items", 2)
        specs = [BatchItemSpec(target_type="npc", params={}) for _ in range(5)]
        with pytest.raises(ContentGenerationError):
            await batch_generator.generate_batch(specs)

    @pytest.mark.asyncio
    async def test_cost_budget_cap(self, batch_generator, monkeypatch):
        monkeypatch.setattr("app.core.content_generator.settings.batch_token_budget", 100)
        monkeypatch.setattr("app.core.content_generator.settings.batch_token_budget_per_item", 50)
        # 3 * 50 = 150 > 100 -> 预估 Token 超限，拒绝
        specs = [BatchItemSpec(target_type="npc", params={}) for _ in range(3)]
        with pytest.raises(ContentGenerationError):
            await batch_generator.generate_batch(specs)

    @pytest.mark.asyncio
    async def test_supported_targets_constant(self):
        assert set(SUPPORTED_BATCH_TARGETS) == {
            "npc",
            "quest",
            "region",
            "settlement",
            "monster",
            "boss",
            "item",
        }


def _make_gen():
    adapter = MockLLMAdapter()
    adapter.mock_response = NPC_MOCK
    return ContentGenerator(
        llm_adapter=adapter,
        template_manager=TemplateManager(),
        quality_scorer=QualityScorer(),
        quality_threshold=0.1,
    )


class TestBatchEndpoint:
    """POST /api/v1/ops/generation/batch 端点级测试。"""

    @pytest.mark.asyncio
    async def test_batch_success_non_persist(self, client, ops_token):
        gen = _make_gen()
        with patch("app.core.content_generator.get_content_generator", return_value=gen):
            resp = await client.post(
                "/api/v1/ops/generation/batch",
                headers={"Authorization": f"Bearer {ops_token}"},
                json={
                    "items": [
                        {"target_type": "npc", "params": {"region_id": "r", "chapter_id": "c"}}
                        for _ in range(2)
                    ]
                },
            )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["total"] == 2
        assert data["succeeded"] == 2
        assert data["failed"] == 0
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_batch_invalid_target_type(self, client, ops_token):
        gen = _make_gen()
        with patch("app.core.content_generator.get_content_generator", return_value=gen):
            resp = await client.post(
                "/api/v1/ops/generation/batch",
                headers={"Authorization": f"Bearer {ops_token}"},
                json={"items": [{"target_type": "unknown", "params": {}}]},
            )
        assert resp.status_code == 400
        assert resp.json()["code"] == GenerationErrorCodes.INVALID_ARGUMENT

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, client, ops_token):
        gen = _make_gen()
        call_count = {"n": 0}

        async def flaky(region_id=None, chapter_id=None, npc_role="commoner", context=None):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise ContentGenerationError("boom")
            return NPC_MOCK

        gen.generate_npc = flaky
        with patch("app.core.content_generator.get_content_generator", return_value=gen):
            resp = await client.post(
                "/api/v1/ops/generation/batch",
                headers={"Authorization": f"Bearer {ops_token}"},
                json={"items": [{"target_type": "npc", "params": {}} for _ in range(2)]},
            )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["succeeded"] == 1
        assert data["failed"] == 1

    @pytest.mark.asyncio
    async def test_batch_persist_creates_objects(self, client, ops_token):
        gen = _make_gen()
        with patch("app.core.content_generator.get_content_generator", return_value=gen):
            resp = await client.post(
                "/api/v1/ops/generation/batch",
                headers={"Authorization": f"Bearer {ops_token}"},
                json={
                    "items": [{"target_type": "npc", "params": {}} for _ in range(2)],
                    "persist": True,
                },
            )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["succeeded"] == 2

        # 直接读库验证持久化（不依赖 GET 端点会话生命周期）
        from app.repositories.generation_repo import GenerationRepository
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as session:
            repo = GenerationRepository(session)
            _objs, total = await repo.list_objects(object_type="npc")
        assert total == 2, f"persisted npc objects expected 2, got {total}"
