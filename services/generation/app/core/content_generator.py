"""基于 LLM 的内容生成器模块。"""

import logging
from typing import Any

from app.core.config import settings
from app.core.llm_adapter import (
    LLMAPIError,
    LLMAdapter,
    LLMRateLimitError,
    LLMTimeoutError,
    get_llm_adapter,
)
from app.core.quality_scorer import QualityScorer
from app.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class ContentGenerationError(Exception):
    """内容生成错误。"""

    def __init__(self, message: str, quality_score: float | None = None):
        super().__init__(message)
        self.quality_score = quality_score


class ContentGenerator:
    """内容生成器，集成 LLM、模板管理和质量评分。"""

    def __init__(
        self,
        llm_adapter: LLMAdapter | None = None,
        template_manager: TemplateManager | None = None,
        quality_scorer: QualityScorer | None = None,
        quality_threshold: float | None = None,
    ):
        self.llm_adapter = llm_adapter or get_llm_adapter()
        self.template_manager = template_manager or TemplateManager(settings.template_dir)
        self.template_manager.load_templates()
        self.quality_scorer = quality_scorer or QualityScorer()
        self.quality_threshold = quality_threshold or settings.quality_threshold

    async def generate_npc(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成 NPC 内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            context: 额外上下文信息

        Returns:
            生成的 NPC 数据

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template = self.template_manager.match_template("npc", region_id, chapter_id)
        if not template:
            raise ContentGenerationError("No matching NPC template found")

        prompt = self._build_npc_prompt(region_id, chapter_id, context)
        system_prompt = self._build_system_prompt("npc")

        try:
            response = await self.llm_adapter.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
            )
        except (LLMAPIError, LLMTimeoutError, LLMRateLimitError) as e:
            logger.error(f"LLM generation failed: {e}")
            raise ContentGenerationError(f"LLM generation failed: {e}")

        # 质量评分
        score_result = self.quality_scorer.score_npc(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"NPC quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        return response

    async def generate_quest(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        quest_type: str = "side",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成任务内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            quest_type: 任务类型（main/side）
            context: 额外上下文信息

        Returns:
            生成的任务数据

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template = self.template_manager.match_template("quest", region_id, chapter_id)
        if not template:
            raise ContentGenerationError("No matching Quest template found")

        prompt = self._build_quest_prompt(region_id, chapter_id, quest_type, context)
        system_prompt = self._build_system_prompt("quest")

        try:
            response = await self.llm_adapter.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
        except (LLMAPIError, LLMTimeoutError, LLMRateLimitError) as e:
            logger.error(f"LLM generation failed: {e}")
            raise ContentGenerationError(f"LLM generation failed: {e}")

        # 质量评分
        score_result = self.quality_scorer.score_quest(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Quest quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        return response

    async def generate_region(
        self,
        chapter_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成区域内容。

        Args:
            chapter_id: 章节 ID
            context: 额外上下文信息

        Returns:
            生成的区域数据

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template = self.template_manager.match_template("region", None, chapter_id)
        if not template:
            raise ContentGenerationError("No matching Region template found")

        prompt = self._build_region_prompt(chapter_id, context)
        system_prompt = self._build_system_prompt("region")

        try:
            response = await self.llm_adapter.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
        except (LLMAPIError, LLMTimeoutError, LLMRateLimitError) as e:
            logger.error(f"LLM generation failed: {e}")
            raise ContentGenerationError(f"LLM generation failed: {e}")

        # 质量评分
        score_result = self.quality_scorer.score_region(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Region quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        return response

    def _build_system_prompt(self, content_type: str) -> str:
        """构建系统提示。"""
        prompts = {
            "npc": "你是一个游戏世界中的NPC设计专家。你需要根据世界观和区域设定，设计出符合背景的NPC角色。返回的JSON必须包含：name（名字）、role（职业）、personality（性格）、faction_id（阵营ID）、region_id（区域ID）、description（描述）、dialogue（对话）。",
            "quest": "你是一个游戏任务设计专家。你需要根据世界观和区域设定，设计出有趣的任务。返回的JSON必须包含：title（标题）、type（类型main/side）、region_id（区域ID）、chapter_id（章节ID）、description（描述）、objectives（目标列表）、rewards（奖励对象）。",
            "region": "你是一个游戏区域设计专家。你需要根据世界观和章节进度，设计出有特色的区域。返回的JSON必须包含：name（名字）、difficulty（难度easy/normal/hard/extreme）、region_id（区域ID）、chapter_id（章节ID）、description（描述）、features（特色列表）。",
        }
        return prompts.get(content_type, "你是一个游戏内容设计专家。请返回有效的JSON格式。")

    def _build_npc_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """构建 NPC 生成提示。"""
        prompt_parts = ["请设计一个NPC角色。"]

        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if context:
            if "faction" in context:
                prompt_parts.append(f"阵营倾向：{context['faction']}")
            if "role" in context:
                prompt_parts.append(f"职业倾向：{context['role']}")

        prompt_parts.append("\n请返回包含以下字段的JSON：")
        prompt_parts.append("- name: NPC名字")
        prompt_parts.append("- role: 职业（如铁匠、商人、守卫等）")
        prompt_parts.append("- personality: 性格特点")
        prompt_parts.append("- faction_id: 阵营ID")
        prompt_parts.append("- region_id: 所在区域ID")
        prompt_parts.append("- description: 详细描述（50-200字）")
        prompt_parts.append("- dialogue: 开场对话（20-50字）")

        return "\n".join(prompt_parts)

    def _build_quest_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        quest_type: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建任务生成提示。"""
        prompt_parts = [f"请设计一个{quest_type}类型的任务。"]

        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if context:
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "difficulty" in context:
                prompt_parts.append(f"难度：{context['difficulty']}")

        prompt_parts.append("\n请返回包含以下字段的JSON：")
        prompt_parts.append("- title: 任务标题")
        prompt_parts.append("- type: 任务类型（main/side）")
        prompt_parts.append("- region_id: 所在区域ID")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- description: 任务描述（50-200字）")
        prompt_parts.append("- objectives: 任务目标列表（字符串数组）")
        prompt_parts.append("- rewards: 奖励对象（包含experience和gold字段）")

        return "\n".join(prompt_parts)

    def _build_region_prompt(
        self,
        chapter_id: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """构建区域生成提示。"""
        prompt_parts = ["请设计一个游戏区域。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if context:
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "difficulty" in context:
                prompt_parts.append(f"建议难度：{context['difficulty']}")

        prompt_parts.append("\n请返回包含以下字段的JSON：")
        prompt_parts.append("- name: 区域名字")
        prompt_parts.append("- difficulty: 难度（easy/normal/hard/extreme）")
        prompt_parts.append("- region_id: 区域ID（格式：region_xxx）")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- description: 区域描述（50-200字）")
        prompt_parts.append("- features: 区域特色列表（字符串数组）")

        return "\n".join(prompt_parts)


# 全局实例
_generator: ContentGenerator | None = None


def get_content_generator() -> ContentGenerator:
    """获取内容生成器实例。"""
    global _generator
    if _generator is None:
        _generator = ContentGenerator()
    return _generator