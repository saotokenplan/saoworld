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
from app.core.npc_data_adapter import NPCDataAdapter
from app.core.quality_scorer import QualityScorer
from app.core.quest_data_adapter import QuestDataAdapter
from app.core.settlement_data_adapter import SettlementDataAdapter
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
        npc_adapter: NPCDataAdapter | None = None,
        quest_adapter: QuestDataAdapter | None = None,
        settlement_adapter: SettlementDataAdapter | None = None,
    ):
        self.llm_adapter = llm_adapter or get_llm_adapter()
        self.template_manager = template_manager or TemplateManager(settings.template_dir)
        self.template_manager.load_templates()
        self.quality_scorer = quality_scorer or QualityScorer()
        self.quality_threshold = quality_threshold or settings.quality_threshold
        self.npc_adapter = npc_adapter or NPCDataAdapter()
        self.quest_adapter = quest_adapter or QuestDataAdapter()
        self.settlement_adapter = settlement_adapter or SettlementDataAdapter()

    async def generate_npc(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        npc_role: str = "commoner",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成 NPC 内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            npc_role: NPC 角色类型（blacksmith/merchant/guard/healer/quest_giver）
            context: 额外上下文信息

        Returns:
            生成的 NPC 数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_npc_template_by_role(npc_role)
        if not template_name:
            template_name = "npc/npc_base.jinja2"

        prompt = self._build_npc_prompt(region_id, chapter_id, npc_role, context)
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

        try:
            response = self.npc_adapter.ensure_minimum_completeness(response, min_completeness=0.95)
        except ValueError as e:
            logger.warning(f"NPC data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_npc(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"NPC quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.npc_adapter.adapt(response)
        return adapted

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
            quest_type: 任务类型（main/side/event/daily）
            context: 额外上下文信息

        Returns:
            生成的任务数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_quest_template_by_type(quest_type)
        if not template_name:
            template_name = "quest/quest_base.jinja2"

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

        try:
            response = self.quest_adapter.ensure_minimum_completeness(response, min_completeness=0.95)
        except ValueError as e:
            logger.warning(f"Quest data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_quest(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Quest quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.quest_adapter.adapt(response)
        return adapted

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

    async def generate_settlement(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        settlement_type: str = "village",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成聚落内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            settlement_type: 聚落类型（village/town/city/camp/fortress/market/outpost）
            context: 额外上下文信息

        Returns:
            生成的聚落数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_settlement_template_by_type(settlement_type)
        if not template_name:
            template_name = "settlement/settlement_base.jinja2"

        prompt = self._build_settlement_prompt(region_id, chapter_id, settlement_type, context)
        system_prompt = self._build_system_prompt("settlement")

        try:
            response = await self.llm_adapter.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
            )
        except (LLMAPIError, LLMTimeoutError, LLMRateLimitError) as e:
            logger.error(f"LLM generation failed: {e}")
            raise ContentGenerationError(f"LLM generation failed: {e}")

        try:
            response = self.settlement_adapter.ensure_minimum_completeness(response, min_completeness=0.90)
        except ValueError as e:
            logger.warning(f"Settlement data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_settlement(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Settlement quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.settlement_adapter.adapt(response)
        return adapted

    def _build_system_prompt(self, content_type: str) -> str:
        """构建系统提示。"""
        prompts = {
            "npc": "你是一个游戏世界中的NPC设计专家。你需要根据世界观和区域设定，设计出符合背景的完整NPC角色。返回的JSON必须包含所有必需字段：npc_key、name、title、gender、age、race、faction_key、region_key、role、location_key、description、personality、traits、voice、backstory、motivation、relationship_map、dialog_style、dialog_nodes、quests_given、quests_related、shop_items、services_offered、location_x、location_y、interaction_radius。确保所有字段填写完整。",
            "quest": "你是一个游戏任务设计专家。你需要根据世界观和区域设定，设计出有趣的任务。返回的JSON必须包含所有必需字段：quest_key、title、description、quest_type（类型main/side/event/daily）、chapter_id、region_key、start_npc_key、end_npc_key、prerequisites、objectives（目标列表，每个目标包含id、description、type、target、completed）、rewards（包含experience、gold、reputation、items）、failure_condition。确保所有字段填写完整。",
            "region": "你是一个游戏区域设计专家。你需要根据世界观和章节进度，设计出有特色的区域。返回的JSON必须包含：name（名字）、difficulty（难度easy/normal/hard/extreme）、region_id（区域ID）、chapter_id（章节ID）、description（描述）、features（特色列表）。",
            "settlement": "你是一个游戏聚落设计专家。你需要根据区域设定和世界观，设计出符合背景的完整聚落。返回的JSON必须包含所有必需字段：settlement_key、name、settlement_type（village/town/city/camp/fortress/market/outpost）、region_key、chapter_id、faction_key、description、population、main_resources、economy_type（agriculture/commerce/mining/hunting/fishing/trade）、status（peaceful/troubled/warring/thriving）、notable_locations、key_npcs、faction_influence、relationships、history、culture、defenses、services、special_features、location_x、location_y。确保所有字段填写完整。",
        }
        return prompts.get(content_type, "你是一个游戏内容设计专家。请返回有效的JSON格式。")

    def _build_npc_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        npc_role: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建 NPC 生成提示。"""
        prompt_parts = [f"请设计一个{npc_role}类型的NPC角色。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "faction" in context:
                prompt_parts.append(f"阵营倾向：{context['faction']}")
            if "faction_key" in context:
                prompt_parts.append(f"阵营ID：{context['faction_key']}")
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- npc_key: NPC唯一标识（格式：npc_xxx）")
        prompt_parts.append("- name: NPC名字")
        prompt_parts.append("- title: NPC头衔")
        prompt_parts.append("- gender: 性别（male/female/other/unknown）")
        prompt_parts.append("- age: 年龄（数字）")
        prompt_parts.append("- race: 种族（human/elf/dwarf/orc等）")
        prompt_parts.append("- faction_key: 阵营ID（格式：faction_xxx，可为空）")
        prompt_parts.append("- region_key: 区域ID（格式：region_xxx）")
        prompt_parts.append("- role: 职业（blacksmith/merchant/guard/healer/quest_giver）")
        prompt_parts.append("- location_key: 位置标识")
        prompt_parts.append("- description: 详细描述（100-200字）")
        prompt_parts.append("- personality: 性格特点列表（至少2个）")
        prompt_parts.append("- traits: 特征列表")
        prompt_parts.append("- voice: 说话风格描述")
        prompt_parts.append("- backstory: 背景故事（200-300字）")
        prompt_parts.append("- motivation: 动机和目标")
        prompt_parts.append("- relationship_map: 关联NPC关系字典")
        prompt_parts.append("- dialog_style: 对话风格描述")
        prompt_parts.append("- dialog_nodes: 对话树节点（至少6个节点）")
        prompt_parts.append("- quests_given: 发布的任务ID列表")
        prompt_parts.append("- quests_related: 相关任务ID列表")
        prompt_parts.append("- shop_items: 出售物品列表")
        prompt_parts.append("- services_offered: 提供服务列表")
        prompt_parts.append("- location_x: 位置X坐标")
        prompt_parts.append("- location_y: 位置Y坐标")
        prompt_parts.append("- interaction_radius: 交互半径")

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

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "faction" in context:
                prompt_parts.append(f"阵营倾向：{context['faction']}")
            if "faction_key" in context:
                prompt_parts.append(f"阵营ID：{context['faction_key']}")
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "start_npc_key" in context:
                prompt_parts.append(f"接取NPC：{context['start_npc_key']}")
            if "end_npc_key" in context:
                prompt_parts.append(f"交付NPC：{context['end_npc_key']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- quest_key: 任务唯一标识（格式：quest_xxx）")
        prompt_parts.append("- title: 任务标题")
        prompt_parts.append("- description: 任务描述（50-200字）")
        prompt_parts.append("- quest_type: 任务类型（main/side/event/daily）")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- region_key: 所在区域ID")
        prompt_parts.append("- start_npc_key: 接取任务的NPC ID")
        prompt_parts.append("- end_npc_key: 交付任务的NPC ID")
        prompt_parts.append("- prerequisites: 前置任务ID列表")
        prompt_parts.append("- objectives: 任务目标列表（每个目标包含id、description、type(story/location/npc/combat/explore/collect/rescue/travel/quest)、target、completed）")
        prompt_parts.append("- rewards: 奖励对象（包含experience、gold、reputation、items）")
        prompt_parts.append("- failure_condition: 失败条件（如时间限制）")

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

    def _build_settlement_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        settlement_type: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建聚落生成提示。"""
        prompt_parts = [f"请设计一个{settlement_type}类型的聚落。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "faction" in context:
                prompt_parts.append(f"阵营倾向：{context['faction']}")
            if "faction_key" in context:
                prompt_parts.append(f"阵营ID：{context['faction_key']}")
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- settlement_key: 聚落唯一标识（格式：settlement_xxx）")
        prompt_parts.append("- name: 聚落名称")
        prompt_parts.append("- settlement_type: 聚落类型（village/town/city/camp/fortress/market/outpost）")
        prompt_parts.append("- region_key: 所在区域ID（格式：region_xxx）")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- faction_key: 阵营ID（格式：faction_xxx，可为空）")
        prompt_parts.append("- description: 聚落描述（100-200字）")
        prompt_parts.append("- population: 人口数量（数字）")
        prompt_parts.append("- main_resources: 主要资源列表（字符串数组）")
        prompt_parts.append("- economy_type: 经济类型（agriculture/commerce/mining/hunting/fishing/trade）")
        prompt_parts.append("- status: 状态（peaceful/troubled/warring/thriving）")
        prompt_parts.append("- notable_locations: 重要地点列表（每个地点包含location_key、name、description）")
        prompt_parts.append("- key_npcs: 关键NPC ID列表")
        prompt_parts.append("- faction_influence: 阵营影响力字典")
        prompt_parts.append("- relationships: 与邻近聚落的关系字典")
        prompt_parts.append("- history: 聚落历史（100-200字）")
        prompt_parts.append("- culture: 文化特色描述")
        prompt_parts.append("- defenses: 防御设施列表")
        prompt_parts.append("- services: 提供服务列表")
        prompt_parts.append("- special_features: 特殊特色列表")
        prompt_parts.append("- location_x: 位置X坐标")
        prompt_parts.append("- location_y: 位置Y坐标")

        return "\n".join(prompt_parts)


_generator: ContentGenerator | None = None


def get_content_generator() -> ContentGenerator:
    """获取内容生成器实例。"""
    global _generator
    if _generator is None:
        _generator = ContentGenerator()
    return _generator