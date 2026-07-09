"""内容生成器测试。"""

import pytest

from app.core.content_generator import ContentGenerator, ContentGenerationError
from app.core.llm_adapter import MockLLMAdapter
from app.core.quality_scorer import QualityScorer
from app.core.template_manager import TemplateManager


class TestContentGenerator:
    """内容生成器测试。"""

    @pytest.fixture
    def generator(self):
        """创建内容生成器实例。"""
        llm_adapter = MockLLMAdapter()
        template_manager = TemplateManager()
        quality_scorer = QualityScorer()
        return ContentGenerator(
            llm_adapter=llm_adapter,
            template_manager=template_manager,
            quality_scorer=quality_scorer,
            quality_threshold=0.75,
        )

    @pytest.mark.asyncio
    async def test_generate_npc(self, generator):
        """测试 NPC 生成。"""
        npc = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
        )

        assert isinstance(npc, dict)
        assert "name" in npc
        assert "role" in npc
        assert "description" in npc

    @pytest.mark.asyncio
    async def test_generate_npc_with_context(self, generator):
        """测试带上下文的 NPC 生成。"""
        npc = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
            context={"faction": "faction_iron_guard", "role": "铁匠"},
        )

        assert isinstance(npc, dict)
        assert "name" in npc

    @pytest.mark.asyncio
    async def test_generate_quest(self, generator):
        """测试任务生成。"""
        quest = await generator.generate_quest(
            region_id="region_core",
            chapter_id="chapter_01",
            quest_type="side",
        )

        assert isinstance(quest, dict)
        assert "title" in quest
        assert "objectives" in quest
        assert "rewards" in quest

    @pytest.mark.asyncio
    async def test_generate_quest_with_context(self, generator):
        """测试带上下文的任务生成。"""
        quest = await generator.generate_quest(
            region_id="region_core",
            chapter_id="chapter_01",
            quest_type="side",
            context={"theme": "探险", "difficulty": "normal"},
        )

        assert isinstance(quest, dict)
        assert "title" in quest

    @pytest.mark.asyncio
    async def test_generate_region(self, generator):
        """测试区域生成。"""
        region = await generator.generate_region(
            chapter_id="chapter_01",
        )

        assert isinstance(region, dict)
        assert "name" in region
        assert "difficulty" in region
        assert "features" in region

    @pytest.mark.asyncio
    async def test_generate_region_with_context(self, generator):
        """测试带上下文的区域生成。"""
        region = await generator.generate_region(
            chapter_id="chapter_01",
            context={"theme": "森林", "difficulty": "normal"},
        )

        assert isinstance(region, dict)
        assert "name" in region


class TestContentGenerationError:
    """内容生成错误测试。"""

    def test_error_creation(self):
        """测试错误创建。"""
        error = ContentGenerationError("Generation failed")
        assert str(error) == "Generation failed"

    def test_error_with_quality_score(self):
        """测试带质量分数的错误。"""
        error = ContentGenerationError("Quality too low", quality_score=0.5)
        assert error.quality_score == 0.5