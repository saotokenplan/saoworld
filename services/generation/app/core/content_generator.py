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
from app.core.boss_data_adapter import BossDataAdapter
from app.core.item_data_adapter import ItemDataAdapter
from app.core.npc_data_adapter import NPCDataAdapter
from app.core.monster_data_adapter import MonsterDataAdapter
from app.core.quality_scorer import QualityScorer
from app.core.quest_data_adapter import QuestDataAdapter
from app.core.region_data_adapter import RegionDataAdapter
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
        monster_adapter: MonsterDataAdapter | None = None,
        boss_adapter: BossDataAdapter | None = None,
        item_adapter: ItemDataAdapter | None = None,
        region_adapter: RegionDataAdapter | None = None,
    ):
        self.llm_adapter = llm_adapter or get_llm_adapter()
        self.template_manager = template_manager or TemplateManager(settings.template_dir)
        self.template_manager.load_templates()
        self.quality_scorer = quality_scorer or QualityScorer()
        self.quality_threshold = quality_threshold or settings.quality_threshold
        self.npc_adapter = npc_adapter or NPCDataAdapter()
        self.quest_adapter = quest_adapter or QuestDataAdapter()
        self.settlement_adapter = settlement_adapter or SettlementDataAdapter()
        self.monster_adapter = monster_adapter or MonsterDataAdapter()
        self.boss_adapter = boss_adapter or BossDataAdapter()
        self.item_adapter = item_adapter or ItemDataAdapter()
        self.region_adapter = region_adapter or RegionDataAdapter()

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
            生成的区域数据（已转换为 world-service 兼容格式）

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

        try:
            response = self.region_adapter.ensure_minimum_completeness(response, min_completeness=0.90)
        except ValueError as e:
            logger.warning(f"Region data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_region(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Region quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.region_adapter.adapt(response)
        return adapted

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

    async def generate_monster(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        monster_type: str = "beast",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成怪物内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            monster_type: 怪物类型（beast/humanoid/undead/mechanical/elemental/demon/dragon/boss）
            context: 额外上下文信息

        Returns:
            生成的怪物数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_monster_template_by_type(monster_type)
        if not template_name:
            template_name = "monster/monster_base.jinja2"

        prompt = self._build_monster_prompt(region_id, chapter_id, monster_type, context)
        system_prompt = self._build_system_prompt("monster")

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
            response = self.monster_adapter.ensure_minimum_completeness(response, min_completeness=0.95)
        except ValueError as e:
            logger.warning(f"Monster data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_monster(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Monster quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.monster_adapter.adapt(response)
        return adapted

    async def generate_boss(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        boss_rank: str = "legendary",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成Boss内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            boss_rank: Boss等级（legendary/mythic）
            context: 额外上下文信息

        Returns:
            生成的Boss数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_monster_template_by_type("boss")
        if not template_name:
            template_name = "monster/monster_base.jinja2"

        prompt = self._build_boss_prompt(region_id, chapter_id, boss_rank, context)
        system_prompt = self._build_system_prompt("boss")

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
            response = self.boss_adapter.ensure_minimum_completeness(response, min_completeness=0.95)
        except ValueError as e:
            logger.warning(f"Boss data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_boss(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Boss quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.boss_adapter.adapt(response)
        return adapted

    async def generate_item(
        self,
        region_id: str | None = None,
        chapter_id: str | None = None,
        item_type: str = "weapon",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成装备内容。

        Args:
            region_id: 区域 ID
            chapter_id: 章节 ID
            item_type: 装备类型（weapon/armor/accessory/consumable/material）
            context: 额外上下文信息

        Returns:
            生成的装备数据（已转换为 world-service 兼容格式）

        Raises:
            ContentGenerationError: 生成失败或质量不达标
        """
        template_name = self.template_manager.get_item_template_by_type(item_type)
        if not template_name:
            template_name = "item/item_base.jinja2"

        prompt = self._build_item_prompt(region_id, chapter_id, item_type, context)
        system_prompt = self._build_system_prompt("item")

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
            response = self.item_adapter.ensure_minimum_completeness(response, min_completeness=0.95)
        except ValueError as e:
            logger.warning(f"Item data completeness check failed: {e}")
            raise ContentGenerationError(str(e))

        score_result = self.quality_scorer.score_item(response)
        if not score_result.is_acceptable():
            logger.warning(
                f"Item quality below threshold: {score_result.score:.2f}, reasons: {score_result.reasons}"
            )
            raise ContentGenerationError(
                f"Quality score {score_result.score:.2f} below threshold {self.quality_threshold}",
                quality_score=score_result.score,
            )

        adapted = self.item_adapter.adapt(response)
        return adapted

    def _build_system_prompt(self, content_type: str) -> str:
        """构建系统提示。"""
        prompts = {
            "npc": (
                "你是一个游戏世界中的NPC设计专家。你需要根据世界观和区域设定，设计出符合背景的完整NPC角色。"
                "返回的JSON必须包含所有必需字段：npc_key、name、title、gender、age、race、faction_key、"
                "region_key、role、location_key、description、personality、traits、voice、backstory、"
                "motivation、relationship_map、dialog_style、dialog_nodes、quests_given、quests_related、"
                "shop_items、services_offered、location_x、location_y、interaction_radius。"
                "确保所有字段填写完整。"
            ),
            "quest": (
                "你是一个游戏任务设计专家。你需要根据世界观和区域设定，设计出有趣的任务。"
                "返回的JSON必须包含所有必需字段：quest_key、title、description、"
                "quest_type（类型main/side/event/daily）、chapter_id、region_key、start_npc_key、"
                "end_npc_key、prerequisites、objectives（目标列表，每个目标包含id、description、"
                "type、target、completed）、rewards（包含experience、gold、reputation、items）、"
                "failure_condition。确保所有字段填写完整。"
            ),
            "region": (
                "你是一个游戏世界设计专家。你需要根据世界观和区域设定，生成详细的区域场景描述。"
                "返回的JSON必须包含所有必需字段：region_key、name、chapter_id、region_type（core/expansion/anomaly/hidden）、"
                "parent_region、description、lore、atmosphere、visual_style（包含terrain_type、color_palette、lighting、architectural_style）、"
                "landmarks（数组，每个包含landmark_key、name、description、type、significance）、danger_level、"
                "recommended_level、accessibility、climate、notable_locations。确保所有字段填写完整。"
            ),
            "settlement": (
                "你是一个游戏聚落设计专家。你需要根据区域设定和世界观，设计出符合背景的完整聚落。"
                "返回的JSON必须包含所有必需字段：settlement_key、name、"
                "settlement_type（village/town/city/camp/fortress/market/outpost）、region_key、"
                "chapter_id、faction_key、description、population、main_resources、"
                "economy_type（agriculture/commerce/mining/hunting/fishing/trade）、"
                "status（peaceful/troubled/warring/thriving）、notable_locations、key_npcs、"
                "faction_influence、relationships、history、culture、defenses、services、"
                "special_features、location_x、location_y。确保所有字段填写完整。"
            ),
            "monster": (
                "你是一个游戏怪物设计专家。你需要根据世界观和区域设定，设计出符合背景的怪物。"
                "返回的JSON必须包含所有必需字段：monster_key、name、monster_type"
                "（beast/humanoid/undead/mechanical/elemental/demon/dragon/boss）、chapter_id、"
                "region_key、level、hp、attack、defense、speed、description、behavior_pattern"
                "（包含aggression、attack_pattern、special_behaviors）、loot_table（掉落表）、"
                "skills（技能列表，每个包含skill_key、name、description、damage_multiplier、cooldown）。"
                "确保所有数值与等级和怪物类型匹配。"
            ),
            "boss": (
                "你是一个游戏Boss设计专家。你需要根据世界观和区域设定，设计出具有挑战性的区域Boss。"
                "返回的JSON必须包含所有必需字段：monster_key、name、chapter_id、region_key、"
                "level、hp、attack、defense、speed、description、behavior_pattern、loot_table、"
                "skills、is_boss(true)、boss_rank(legendary/mythic)、phase_count、"
                "special_skills（特殊技能列表，每个包含skill_key、name、description、cooldown）、"
                "enrage_threshold（0-1之间的浮点数）、reward（包含experience、items）。"
                "确保Boss具有多个阶段、独特的特殊技能和丰富的奖励。"
            ),
            "item": (
                "你是一个游戏装备设计专家。你需要根据世界观和区域设定，设计出符合背景的装备物品。"
                "返回的JSON必须包含所有必需字段：item_key、item_type（weapon/armor/accessory/consumable/material）、"
                "item_slot（head/chest/legs/feet/weapon/off_hand/ring/necklace，consumable和material为null）、"
                "name、description、rarity（common/uncommon/rare/epic/legendary）、chapter_id、"
                "level_requirement、stats（属性对象）、effects（效果对象）、sell_price、stackable。"
                "确保数值与等级要求和稀有度匹配。"
            ),
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
        prompt_parts.append(
            "- objectives: 任务目标列表（每个目标包含id、description、"
            "type(story/location/npc/combat/explore/collect/rescue/travel/quest)、target、completed）"
        )
        prompt_parts.append("- rewards: 奖励对象（包含experience、gold、reputation、items）")
        prompt_parts.append("- failure_condition: 失败条件（如时间限制）")

        return "\n".join(prompt_parts)

    def _build_region_prompt(
        self,
        chapter_id: str | None,
        context: dict[str, Any] | None,
    ) -> str:
        """构建区域生成提示。"""
        prompt_parts = ["请设计一个游戏区域场景描述。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if context:
            if "region_id" in context:
                prompt_parts.append(f"区域ID：{context['region_id']}")
            if "region_type" in context:
                prompt_parts.append(f"区域类型：{context['region_type']}")
            if "parent_region" in context:
                prompt_parts.append(f"父区域：{context['parent_region']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- region_key: 区域唯一标识（格式：region_xxx）")
        prompt_parts.append("- name: 区域名称（符合世界观风格的中文名称）")
        prompt_parts.append("- chapter_id: 所属章节ID（格式：chapter_xxx）")
        prompt_parts.append("- region_type: 区域类型（core/expansion/anomaly/hidden）")
        prompt_parts.append("- parent_region: 父区域ID（顶级区域为null）")
        prompt_parts.append("- description: 区域描述（200-500字，包含地理特征、气候环境、历史背景）")
        prompt_parts.append("- lore: 区域传说（100-300字，包含区域的神秘故事或历史事件）")
        prompt_parts.append("- atmosphere: 氛围描述（50-100字，描述区域给人的整体感觉）")
        prompt_parts.append("- visual_style: 视觉风格对象，包含：")
        prompt_parts.append("  - terrain_type: 地形类型（plains/forest/mountain/desert/swamp/cave/city/wasteland/volcanic/ocean/lake/river/glacier/jungle）")
        prompt_parts.append("  - color_palette: 主色调数组（3-5个颜色描述）")
        prompt_parts.append("  - lighting: 光照描述（day/night/dark/foggy/sunny）")
        prompt_parts.append("  - architectural_style: 建筑风格（medieval/futuristic/ruined/natural/organic）")
        prompt_parts.append("- landmarks: 地标数组，每个地标包含：")
        prompt_parts.append("  - landmark_key: 地标ID（格式：landmark_xxx）")
        prompt_parts.append("  - name: 地标名称")
        prompt_parts.append("  - description: 地标描述（50-100字）")
        prompt_parts.append("  - type: 地标类型（natural/manmade/ruin/mystical）")
        prompt_parts.append("  - significance: 重要性描述")
        prompt_parts.append("- danger_level: 危险等级（peaceful/low/medium/high/extreme）")
        prompt_parts.append("- recommended_level: 推荐等级范围（格式：\"1-10\"）")
        prompt_parts.append("- accessibility: 可访问性描述（如何到达这个区域）")
        prompt_parts.append("- climate: 气候描述（温度、天气特点）")
        prompt_parts.append("- notable_locations: 著名地点数组（5-10个简短地点名称）")

        # === WP1 实施期提示词硬化（A4/A5，详见 docs/10-requirements/M4-模板文本细化.md）===
        # A4 (F4) 章节强度上限条款（场景部分）
        prompt_parts.append("")
        prompt_parts.append("【章节一致性约束（F4）】")
        prompt_parts.append("- 本章为 chapter_N 时，场景 recommended_level 必须与同章节怪物等级带 [10 × (N-1) + 1, 10 × N + 2] 一致")
        prompt_parts.append("- 生成后请自检：上述数值字段是否满足章节上限，不满足请修正后再返回")
        # A5 (F6) 输出格式硬化
        prompt_parts.append("")
        prompt_parts.append("【输出格式要求（F6）】")
        prompt_parts.append("- 仅返回一个 JSON 对象，不要返回任何解释文字、前后缀或 markdown 代码围栏")
        prompt_parts.append("- 返回前逐项自检上述必需字段：缺失任一字段即视为不合格输出，请补全后再返回")

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

    def _build_monster_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        monster_type: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建怪物生成提示。"""
        prompt_parts = [f"请设计一个{monster_type}类型的怪物。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "difficulty" in context:
                prompt_parts.append(f"难度：{context['difficulty']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- monster_key: 怪物唯一标识（格式：monster_xxx）")
        prompt_parts.append("- name: 怪物名称")
        prompt_parts.append("- monster_type: 怪物类型（beast/humanoid/undead/mechanical/elemental/demon/dragon/boss）")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- region_key: 所在区域ID（格式：region_xxx）")
        prompt_parts.append("- level: 等级（1-60的整数）")
        prompt_parts.append("- hp: 生命值（正整数）")
        prompt_parts.append("- attack: 攻击力（非负整数）")
        prompt_parts.append("- defense: 防御力（非负整数）")
        prompt_parts.append("- speed: 速度（非负整数，1-20）")
        prompt_parts.append("- description: 怪物描述（50-200字）")
        prompt_parts.append("- behavior_pattern: 行为模式对象")
        prompt_parts.append("  - aggression: 攻击性（passive/defensive/aggressive/berserker）")
        prompt_parts.append("  - attack_pattern: 攻击模式（melee/ranged/magic/mixed）")
        prompt_parts.append("  - special_behaviors: 特殊行为列表")
        prompt_parts.append("- loot_table: 掉落表数组（每个元素包含item_key、drop_rate、quantity_min、quantity_max）")
        prompt_parts.append("- skills: 技能数组（每个技能包含skill_key、name、description、damage_multiplier、cooldown）")

        # === WP1 实施期提示词硬化（A3/A4/A5，详见 docs/10-requirements/M4-模板文本细化.md）===
        # A3 (F3) 怪物数值锚定表
        prompt_parts.append("")
        prompt_parts.append("【数值锚定要求（F3）】怪物数值必须落在以下区间，允许 ±20% 浮动：")
        prompt_parts.append("- hp 基值 = 40 + 26 × level，乘以类型系数")
        prompt_parts.append("- attack 基值 = 3 + 2.2 × level，乘以类型系数")
        prompt_parts.append("- defense 基值 = 2 + 1.5 × level（不乘类型系数）")
        prompt_parts.append("- 类型系数：beast=1.0，humanoid=0.9，undead=1.1，mechanical=1.2，elemental=0.95，demon=1.15，dragon=1.3")
        prompt_parts.append("- speed 维持 1-20，与体型/类型相符（dragon/mechanical 偏慢，elemental 偏快）")
        prompt_parts.append("- skills 的 damage_multiplier 区间 0.8-2.0（普通怪物），cooldown ≥ 3 秒")
        # A4 (F4) 章节强度上限条款（怪物部分）
        prompt_parts.append("")
        prompt_parts.append("【章节一致性约束（F4）】")
        prompt_parts.append("- 本章为 chapter_N 时，怪物 level 必须落在 [10 × (N-1) + 1, 10 × N + 2] 区间")
        prompt_parts.append("- 生成后请自检：上述数值字段是否同时满足数值锚定与章节上限，不满足请修正后再返回")
        # A5 (F6) 输出格式硬化
        prompt_parts.append("")
        prompt_parts.append("【输出格式要求（F6）】")
        prompt_parts.append("- 仅返回一个 JSON 对象，不要返回任何解释文字、前后缀或 markdown 代码围栏")
        prompt_parts.append("- 返回前逐项自检上述必需字段：缺失任一字段即视为不合格输出，请补全后再返回")

        return "\n".join(prompt_parts)

    def _build_boss_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        boss_rank: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建Boss生成提示。"""
        prompt_parts = [f"请设计一个{boss_rank}等级的区域Boss。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "difficulty" in context:
                prompt_parts.append(f"难度：{context['difficulty']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- monster_key: Boss唯一标识（格式：boss_xxx）")
        prompt_parts.append("- name: Boss名称（富有史诗感）")
        prompt_parts.append("- chapter_id: 所属章节ID")
        prompt_parts.append("- region_key: 所在区域ID（格式：region_xxx）")
        prompt_parts.append("- level: 等级（5-60的整数，Boss应高于区域普通怪物）")
        prompt_parts.append("- hp: 生命值（至少100，Boss应显著高于普通怪物）")
        prompt_parts.append("- attack: 攻击力（至少10）")
        prompt_parts.append("- defense: 防御力（至少5）")
        prompt_parts.append("- speed: 速度（1-20的整数）")
        prompt_parts.append("- description: Boss描述（100-300字，包含背景故事）")
        prompt_parts.append("- behavior_pattern: 行为模式对象")
        prompt_parts.append("  - aggression: 攻击性（aggressive/berserker）")
        prompt_parts.append("  - attack_pattern: 攻击模式（melee/ranged/magic/mixed）")
        prompt_parts.append("  - special_behaviors: 特殊行为列表（如enrage、phase_change）")
        prompt_parts.append("- loot_table: 掉落表数组（每个元素包含item_key、drop_rate、quantity_min、quantity_max）")
        prompt_parts.append("- skills: 普通技能数组（至少2个，每个技能包含skill_key、name、description、damage_multiplier、cooldown）")
        prompt_parts.append("- is_boss: 是否为Boss（固定为true）")
        prompt_parts.append("- boss_rank: Boss等级（legendary/mythic）")
        prompt_parts.append("- phase_count: 阶段数量（1-5的整数）")
        prompt_parts.append("- special_skills: 特殊技能数组（每个阶段至少1个，包含skill_key、name、description、cooldown）")
        prompt_parts.append("- enrage_threshold: 狂暴阈值（0-1之间的浮点数，生命值低于此值时狂暴）")
        prompt_parts.append("- reward: 击杀奖励对象")
        prompt_parts.append("  - experience: 经验值（应高于同等级普通怪物的3-5倍）")
        prompt_parts.append("  - items: 物品奖励列表（包含稀有装备或材料）")
        prompt_parts.append("- min_reputation: 最低声望要求（0或正数）")

        # === WP1 实施期提示词硬化（A3/A4/A5，详见 docs/10-requirements/M4-模板文本细化.md）===
        # A3 (F3) Boss 显式引用 3.2 怪物数值锚定公式
        prompt_parts.append("")
        prompt_parts.append("【Boss 数值锚定要求（F3 引用）】")
        prompt_parts.append("- 同等级普通怪物基值：hp 基值 = 40 + 26 × level，attack 基值 = 3 + 2.2 × level，defense 基值 = 2 + 1.5 × level（类型系数同 3.2）")
        prompt_parts.append("- Boss 须达到：hp ≥ 5 × 同等级普通怪物基值，attack ≥ 2 × 同等级普通怪物基值")
        prompt_parts.append("- reward.experience 应为同等级普通怪物的 3-5 ×")
        # A4 (F4) 章节强度上限条款（Boss 部分）
        prompt_parts.append("")
        prompt_parts.append("【章节一致性约束（F4）】")
        prompt_parts.append("- 本章为 chapter_N 时，Boss level 必须落在 [10 × (N-1) + 1, 10 × N + 2] 区间内（且应高于同区域普通怪物）")
        prompt_parts.append("- 生成后请自检：上述数值字段是否同时满足数值锚定与章节上限，不满足请修正后再返回")
        # A5 (F6) 输出格式硬化
        prompt_parts.append("")
        prompt_parts.append("【输出格式要求（F6）】")
        prompt_parts.append("- 仅返回一个 JSON 对象，不要返回任何解释文字、前后缀或 markdown 代码围栏")
        prompt_parts.append("- 返回前逐项自检上述必需字段：缺失任一字段即视为不合格输出，请补全后再返回")

        return "\n".join(prompt_parts)

    def _build_item_prompt(
        self,
        region_id: str | None,
        chapter_id: str | None,
        item_type: str,
        context: dict[str, Any] | None,
    ) -> str:
        """构建装备生成提示。"""
        prompt_parts = [f"请设计一个{item_type}类型的装备。"]

        if chapter_id:
            prompt_parts.append(f"章节：{chapter_id}")
        if region_id:
            prompt_parts.append(f"区域：{region_id}")
        if context:
            if "region_key" in context:
                prompt_parts.append(f"区域ID：{context['region_key']}")
            if "world_rules" in context:
                prompt_parts.append(f"世界规则：{context['world_rules']}")
            if "theme" in context:
                prompt_parts.append(f"主题：{context['theme']}")
            if "rarity" in context:
                prompt_parts.append(f"建议稀有度：{context['rarity']}")
            if "level" in context:
                prompt_parts.append(f"建议等级：{context['level']}")

        prompt_parts.append("\n请返回包含以下所有字段的完整JSON：")
        prompt_parts.append("- item_key: 装备唯一标识（格式：item_xxx）")
        prompt_parts.append("- item_type: 装备类型（weapon/armor/accessory/consumable/material）")
        prompt_parts.append("- item_slot: 装备槽位（head/chest/legs/feet/weapon/off_hand/ring/necklace，consumable和material为null）")
        prompt_parts.append("- name: 装备名称（符合类型和稀有度的命名风格）")
        prompt_parts.append("- description: 装备描述（30-100字，包含外观和背景故事）")
        prompt_parts.append("- rarity: 稀有度（common/uncommon/rare/epic/legendary）")
        prompt_parts.append("- chapter_id: 所属章节ID（格式：chapter_xxx）")
        prompt_parts.append("- level_requirement: 等级要求（1-60的整数）")
        prompt_parts.append("- stats: 属性对象（可包含attack、defense、max_hp、max_mp、speed、critical_rate、critical_damage）")
        prompt_parts.append("- effects: 效果对象（包含effect_type、duration、cooldown、description）")
        prompt_parts.append("- sell_price: 售卖价格（非负整数）")
        prompt_parts.append("- stackable: 是否可堆叠（consumable和material为true，其他为false）")

        # === WP1 实施期提示词硬化（A3/A4/A5，详见 docs/10-requirements/M4-模板文本细化.md）===
        # A3 (F2) 装备数值锚定表
        prompt_parts.append("")
        prompt_parts.append("【数值锚定要求（F2）】装备数值必须落在以下区间，允许 ±20% 浮动：")
        prompt_parts.append("- weapon 的 attack 基值 = 6 + 4 × level_requirement，再乘以稀有度系数")
        prompt_parts.append("- armor 的 defense 基值 = 3 + 2.5 × level_requirement，再乘以稀有度系数")
        prompt_parts.append("- 稀有度系数：common=1.0，uncommon=1.2，rare=1.5，epic=1.9，legendary=2.4")
        prompt_parts.append("- max_hp 加成 ≤ 50 × level_requirement × 稀有度系数；max_mp 同理上限减半")
        prompt_parts.append("- critical_rate 上限：common 0.05 / uncommon 0.08 / rare 0.12 / epic 0.16 / legendary 0.20")
        prompt_parts.append("- critical_damage 区间 1.2-2.5，随稀有度递增")
        prompt_parts.append("- sell_price 基值 = 10 × level_requirement × 稀有度系数（取整）")
        # A4 (F4) 章节强度上限条款（装备部分）
        prompt_parts.append("")
        prompt_parts.append("【章节一致性约束（F4）】")
        prompt_parts.append("- 本章为 chapter_N 时，装备 level_requirement 不得高于 10 × N")
        prompt_parts.append("- 生成后请自检：上述数值字段是否同时满足数值锚定与章节上限，不满足请修正后再返回")
        # A5 (F6) 输出格式硬化
        prompt_parts.append("")
        prompt_parts.append("【输出格式要求（F6）】")
        prompt_parts.append("- 仅返回一个 JSON 对象，不要返回任何解释文字、前后缀或 markdown 代码围栏")
        prompt_parts.append("- 返回前逐项自检上述必需字段：缺失任一字段即视为不合格输出，请补全后再返回")

        return "\n".join(prompt_parts)


_generator: ContentGenerator | None = None


def get_content_generator() -> ContentGenerator:
    """获取内容生成器实例。"""
    global _generator
    if _generator is None:
        _generator = ContentGenerator()
    return _generator
