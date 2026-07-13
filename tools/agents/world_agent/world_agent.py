from typing import Dict, List, Optional, Any
from uuid import uuid4
from world_input_schemas import WorldTaskInput, RequirementItem
from world_output_schemas import (
    NPCConfig,
    QuestConfig,
    Objective,
    RegionConfig,
    RegionScope,
    EventConfig,
    ContentPackageOutput,
    ReviewRequest,
    WorldGenerationResult,
)
from world_error_handler import (
    MissingSkeletonError,
    TemplateMismatchError,
    ContentViolationError,
    ReviewFailedError,
    HighDuplicationError,
    handle_missing_skeleton,
    handle_template_mismatch,
    handle_content_violation,
    handle_review_failed,
    handle_high_duplication,
)


class WorldAgent:
    def __init__(self):
        self.input_data: Dict[str, Any] = {}
        self.validation_result: Dict[str, Any] = {}
        self.template_match: Dict[str, Any] = {}
        self.generated_npcs: List[NPCConfig] = []
        self.generated_quests: List[QuestConfig] = []
        self.generated_regions: List[RegionConfig] = []
        self.generated_events: List[EventConfig] = []
        self.content_package: Optional[ContentPackageOutput] = None
        self.review_request: Optional[ReviewRequest] = None
        self.errors: List[str] = []

    def read_input_data(self, task_input: WorldTaskInput) -> Dict[str, Any]:
        world_rules = task_input.world_rules

        input_summary = {
            "world_version": world_rules.world_version,
            "chapter_id": world_rules.chapter_id,
            "regions_count": len(world_rules.regions),
            "factions_count": len(world_rules.factions),
            "forbidden_tags_count": len(world_rules.forbidden_tags),
            "has_vote_result": task_input.vote_result is not None,
            "has_template": task_input.template is not None,
            "has_skeleton_snapshot": task_input.skeleton_snapshot is not None,
            "has_design_note": task_input.design_note is not None,
        }

        if task_input.vote_result:
            input_summary["winning_direction"] = task_input.vote_result.winning_direction
            input_summary["voter_count"] = task_input.vote_result.voter_count

        if task_input.template:
            input_summary["template_type"] = task_input.template.type
            input_summary["template_fields_count"] = len(task_input.template.fields)

        self.input_data = input_summary
        return input_summary

    def validate_input(self, task_input: WorldTaskInput) -> Dict[str, Any]:
        world_rules = task_input.world_rules
        errors: List[str] = []

        if task_input.skeleton_snapshot is None:
            errors.append("缺少骨架快照")
        else:
            snapshot = task_input.skeleton_snapshot
            if not snapshot.forbidden_tags:
                errors.append("骨架快照缺少 forbidden_tags")
            if not snapshot.chapter_id:
                errors.append("骨架快照缺少 chapter_id")

        if not world_rules.chapter_id:
            errors.append("世界规则缺少 chapter_id")

        if task_input.template:
            if task_input.template.schema_version < 1:
                errors.append("模板版本不兼容")

        if task_input.vote_result:
            pass

        validation_result = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
        }

        if not validation_result["is_valid"]:
            raise MissingSkeletonError(f"输入校验失败: {'; '.join(errors)}")

        self.validation_result = validation_result
        return validation_result

    def match_template(self, task_input: WorldTaskInput) -> Dict[str, Any]:
        content_type = "npc"
        if task_input.design_note:
            content_type = task_input.design_note.content_type
        elif task_input.vote_result:
            content_type = "region"

        template = task_input.template

        if template is None:
            matched_template = self._get_default_template(content_type)
        else:
            if template.type != content_type:
                raise TemplateMismatchError(
                    f"模板类型 {template.type} 与所需类型 {content_type} 不匹配"
                )
            matched_template = {
                "template_id": template.template_id,
                "type": template.type,
                "schema_version": template.schema_version,
                "fields": {f.name: f.options or [] for f in template.fields},
            }

        self.template_match = matched_template
        return matched_template

    def _get_default_template(self, content_type: str) -> Dict[str, Any]:
        templates = {
            "npc": {
                "template_id": "tpl_npc_default",
                "type": "npc",
                "schema_version": 1,
                "fields": {
                    "name": [],
                    "title": [],
                    "faction_id": [],
                    "personality": ["friendly", "neutral", "grumpy", "mysterious"],
                    "skills": ["crafting", "trading", "healing", "combat", "nature"],
                    "dialog_templates": ["greeting", "quest_offer", "farewell"],
                },
            },
            "quest": {
                "template_id": "tpl_quest_default",
                "type": "quest",
                "schema_version": 1,
                "fields": {
                    "name": [],
                    "type": ["main", "side"],
                    "objectives": ["explore", "defeat", "collect", "talk"],
                    "rewards": [],
                },
            },
            "region": {
                "template_id": "tpl_region_default",
                "type": "region",
                "schema_version": 1,
                "fields": {
                    "name": [],
                    "biome": ["forest", "desert", "mountain", "swamp", "coastal"],
                    "climate": ["temperate", "tropical", "arid", "frigid", "misty"],
                    "resources": [],
                    "dangers": [],
                },
            },
            "event": {
                "template_id": "tpl_event_default",
                "type": "event",
                "schema_version": 1,
                "fields": {
                    "name": [],
                    "type": ["raid", "discovery", "trade", "conflict"],
                    "impact": ["minor", "major", "critical"],
                    "duration": ["temporary", "permanent"],
                },
            },
        }
        return templates.get(content_type, templates["npc"])

    def generate_content(self, task_input: WorldTaskInput, content_type: str = "npc") -> List[Any]:
        if content_type == "npc":
            return self._generate_npcs(task_input)
        elif content_type == "quest":
            return self._generate_quests(task_input)
        elif content_type == "region":
            return self._generate_regions(task_input)
        elif content_type == "event":
            return self._generate_events(task_input)
        else:
            return []

    def _generate_npcs(self, task_input: WorldTaskInput) -> List[NPCConfig]:
        world_rules = task_input.world_rules
        region_id = world_rules.regions[0].region_id if world_rules.regions else "region_unknown"
        faction_id = world_rules.factions[0].faction_id if world_rules.factions else "faction_unknown"

        npc = NPCConfig(
            npc_id=f"npc_{uuid4().hex[:8]}",
            name="待定NPC",
            title="旅行者",
            faction_id=faction_id,
            region_id=region_id,
            personality="neutral",
            skills=["exploration"],
            dialogs={
                "greeting": "你好，旅行者...",
                "quest_offer": "我有一件事需要你的帮助...",
                "farewell": "祝你好运...",
            },
        )

        self.generated_npcs = [npc]
        return [npc]

    def _generate_quests(self, task_input: WorldTaskInput) -> List[QuestConfig]:
        world_rules = task_input.world_rules
        region_id = world_rules.regions[0].region_id if world_rules.regions else "region_unknown"
        npc_id = self.generated_npcs[0].npc_id if self.generated_npcs else "npc_unknown"

        quest = QuestConfig(
            quest_id=f"quest_{uuid4().hex[:8]}",
            name="待定任务",
            type="side",
            region_id=region_id,
            npc_id=npc_id,
            objectives=[
                Objective(type="explore", target="目标区域", count=1),
            ],
            rewards={"gold": 100, "exp": 500},
            prerequisites=[],
        )

        self.generated_quests = [quest]
        return [quest]

    def _generate_regions(self, task_input: WorldTaskInput) -> List[RegionConfig]:
        region = RegionConfig(
            region_id=f"region_{uuid4().hex[:8]}",
            name="待定区域",
            description="一片神秘的未知领域，等待着冒险者的探索...",
            status="locked",
            level_range={"min": 5, "max": 10},
            region_scope=RegionScope(
                biome="forest",
                climate="temperate",
                resources=["wood", "herbs"],
                dangers=["wild_beasts"],
            ),
        )

        self.generated_regions = [region]
        return [region]

    def _generate_events(self, task_input: WorldTaskInput) -> List[EventConfig]:
        world_rules = task_input.world_rules
        region_id = world_rules.regions[0].region_id if world_rules.regions else "region_unknown"

        event = EventConfig(
            event_id=f"event_{uuid4().hex[:8]}",
            name="待定事件",
            type="discovery",
            region_id=region_id,
            description="一个不寻常的发现引起了冒险者的注意...",
            impact="minor",
            duration="temporary",
        )

        self.generated_events = [event]
        return [event]

    def apply_rules(self, task_input: WorldTaskInput) -> Dict[str, Any]:
        world_rules = task_input.world_rules
        checks: Dict[str, Any] = {
            "world_consistency": "passed",
            "reward_boundary": "passed",
            "content_safety": "passed",
            "duplication": "passed",
        }

        for tag in world_rules.forbidden_tags:
            for npc in self.generated_npcs:
                npc_text = f"{npc.name} {npc.title} {' '.join(npc.dialogs.values())}"
                if tag.lower() in npc_text.lower():
                    raise ContentViolationError(f"NPC内容包含禁止标签: {tag}")

        for quest in self.generated_quests:
            if "gold" in quest.rewards:
                gold_reward = quest.rewards["gold"]
                if isinstance(gold_reward, int):
                    max_gold = world_rules.reward_limits.gold.get("max", 1000)
                    if gold_reward > max_gold:
                        checks["reward_boundary"] = "failed"

            if "exp" in quest.rewards:
                exp_reward = quest.rewards["exp"]
                if isinstance(exp_reward, int):
                    max_exp = world_rules.reward_limits.exp.get("max", 5000)
                    if exp_reward > max_exp:
                        checks["reward_boundary"] = "failed"

        return checks

    def refine_text(self, task_input: WorldTaskInput) -> Dict[str, Any]:
        refinement_result: Dict[str, Any] = {
            "npc_count": len(self.generated_npcs),
            "quest_count": len(self.generated_quests),
            "region_count": len(self.generated_regions),
            "event_count": len(self.generated_events),
            "refined": True,
        }

        for npc in self.generated_npcs:
            if npc.name == "待定NPC":
                npc.name = "神秘的旅者"
            if "你好，旅行者..." in npc.dialogs.get("greeting", ""):
                npc.dialogs["greeting"] = "欢迎来到这片土地，陌生人。这里有许多故事等待你去发现..."

        for quest in self.generated_quests:
            if quest.name == "待定任务":
                quest.name = "未知的探索"
            for obj in quest.objectives:
                if obj.target == "目标区域":
                    obj.target = "神秘之地"

        for region in self.generated_regions:
            if region.name == "待定区域":
                region.name = "神秘领域"
            if "未知领域" in region.description:
                region.description = "一片被迷雾笼罩的古老土地，传说中隐藏着失落的宝藏和被遗忘的文明..."

        for event in self.generated_events:
            if event.name == "待定事件":
                event.name = "异常波动"
            if "不寻常的发现" in event.description:
                event.description = "空气中出现了异样的波动，经验丰富的冒险者感受到了潜在的危险..."

        return refinement_result

    def package_content(self, task_input: WorldTaskInput) -> ContentPackageOutput:
        world_rules = task_input.world_rules
        region_id = ""
        if self.generated_regions:
            region_id = self.generated_regions[0].region_id
        elif world_rules.regions:
            region_id = world_rules.regions[0].region_id

        content: Dict[str, List] = {}
        if self.generated_npcs:
            content["npcs"] = [npc.model_dump() for npc in self.generated_npcs]
        if self.generated_quests:
            content["quests"] = [quest.model_dump() for quest in self.generated_quests]
        if self.generated_events:
            content["events"] = [event.model_dump() for event in self.generated_events]
        if self.generated_regions:
            content["regions"] = [region.model_dump() for region in self.generated_regions]

        content_package = ContentPackageOutput(
            content_package_id=f"pkg_{uuid4().hex[:12]}",
            version="1.0",
            chapter_id=world_rules.chapter_id,
            region_id=region_id,
            type="region",
            content=content,
        )

        self.content_package = content_package
        return content_package

    def submit_for_review(self, task_input: WorldTaskInput) -> ReviewRequest:
        if not self.content_package:
            self.package_content(task_input)

        review_request = ReviewRequest(
            request_id=f"gen_{uuid4().hex[:12]}",
            content_package_id=self.content_package.content_package_id if self.content_package else "",
            type="content_review",
            checks=["world_consistency", "reward_boundary", "content_safety", "duplication"],
            priority="normal",
        )

        self.review_request = review_request
        return review_request

    def handle_review_result(self, review_result: str = "approved") -> Dict[str, Any]:
        if review_result == "approved":
            return {"action": "notify_build_agent", "status": "approved"}
        elif review_result == "rejected":
            raise ReviewFailedError("内容审核被拒绝，需要重新生成")
        elif review_result == "needs_revision":
            return {"action": "revise_content", "status": "needs_revision", "feedback": "根据审核反馈调整内容"}
        else:
            return {"action": "unknown", "status": review_result}

    def apply_requirement_to_content(self, requirement: RequirementItem) -> Dict[str, Any]:
        """根据需求包调整生成的内容

        Args:
            requirement: 需求包

        Returns:
            应用结果
        """
        scope = requirement.target_scope
        applied: Dict[str, Any] = {
            "requirement_id": requirement.requirement_id,
            "scope": scope,
            "applied_to": [],
        }

        if scope in ("world", "npc") and self.generated_npcs:
            for npc in self.generated_npcs:
                if "探索" in requirement.title or "区域" in requirement.title:
                    npc.skills.append("exploration")
                    npc.dialogs["quest_offer"] = (
                        f"听说你对探索很感兴趣？我这里有一个关于{requirement.title[:10]}的任务..."
                    )
                applied["applied_to"].append(f"npc:{npc.npc_id}")

        if scope in ("world", "quest") and self.generated_quests:
            for quest in self.generated_quests:
                if "支线" in requirement.description or "完成率" in requirement.description:
                    quest.type = "side"
                    quest.rewards["gold"] = int(quest.rewards.get("gold", 100) * 1.2)
                    quest.rewards["exp"] = int(quest.rewards.get("exp", 500) * 1.2)
                applied["applied_to"].append(f"quest:{quest.quest_id}")

        if scope in ("world", "region") and self.generated_regions:
            for region in self.generated_regions:
                if "热门" in requirement.title or "访问量" in requirement.description:
                    region.description += (
                        " 这里最近变得异常热闹，各地的冒险者都被吸引而来。"
                    )
                applied["applied_to"].append(f"region:{region.region_id}")

        return applied

    def generate_from_requirement(
        self,
        requirement: RequirementItem,
        task_input: WorldTaskInput,
    ) -> Dict[str, Any]:
        """基于需求包生成内容

        Args:
            requirement: 需求包
            task_input: 基础任务输入（含世界规则、骨架快照等）

        Returns:
            生成结果
        """
        scope = requirement.target_scope

        content_types: List[str] = []
        if scope == "all":
            content_types = ["npc", "quest", "region", "event"]
        elif scope == "npc":
            content_types = ["npc"]
        elif scope == "quest":
            content_types = ["quest"]
        elif scope == "world":
            content_types = ["npc", "quest", "region"]
        else:
            content_types = [scope] if scope in ("npc", "quest", "region", "event") else ["npc"]

        self.read_input_data(task_input)
        self.validate_input(task_input)
        self.match_template(task_input)

        for ct in content_types:
            self.generate_content(task_input, ct)

        self.apply_requirement_to_content(requirement)
        self.apply_rules(task_input)
        self.refine_text(task_input)
        self.package_content(task_input)
        self.submit_for_review(task_input)

        return {
            "content_types": content_types,
            "npc_count": len(self.generated_npcs),
            "quest_count": len(self.generated_quests),
            "region_count": len(self.generated_regions),
            "event_count": len(self.generated_events),
            "content_package_id": self.content_package.content_package_id if self.content_package else "",
            "requirement_applied": True,
        }

    def execute_requirement_driven_generation(
        self,
        task_id: str = "",
        params: Optional[Dict[str, Any]] = None,
        input_from_requirement_task: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Orchestrator 调用入口：需求驱动的内容生成

        支持从上游需求生成任务获取输入
        """
        from world_input_schemas import WorldRules, SkeletonSnapshot

        if params is None:
            params = {}

        requirements = []
        if input_from_requirement_task and "requirements" in input_from_requirement_task:
            requirements = input_from_requirement_task["requirements"]

        requirement_data = requirements[0] if requirements else {
            "requirement_id": "req_unknown",
            "title": "数据驱动内容生成",
            "description": "基于数据洞察生成的内容",
            "priority": "P2",
            "target_scope": params.get("target_scope", "world"),
            "quality_score": 0.7,
        }

        requirement = RequirementItem(**requirement_data)

        world_rules = WorldRules(
            world_version="1.0",
            chapter_id=params.get("chapter_id", "chapter_01"),
            regions=[],
            factions=[],
            forbidden_tags=["暴力", "色情"],
        )

        skeleton = SkeletonSnapshot(
            skeleton_id="skel_default",
            world_version="1.0",
            chapter_id=world_rules.chapter_id,
            regions=[],
            factions=[],
            forbidden_tags=["暴力", "色情"],
            status="active",
        )

        task_input = WorldTaskInput(
            world_rules=world_rules,
            skeleton_snapshot=skeleton,
            requirement=requirement,
        )

        result = self.generate_from_requirement(requirement, task_input)

        return {
            "task_id": task_id,
            "requirement_id": requirement.requirement_id,
            "content_generated": True,
            **result,
        }

    def execute_world_generation_flow(
        self,
        task_input: WorldTaskInput,
        content_types: List[str] | None = None,
    ) -> WorldGenerationResult:
        try:
            self.read_input_data(task_input)
            self.validate_input(task_input)
            self.match_template(task_input)

            if content_types is None:
                content_types = ["npc", "quest", "region", "event"]

            for ct in content_types:
                self.generate_content(task_input, ct)

            self.apply_rules(task_input)
            self.refine_text(task_input)
            self.package_content(task_input)
            self.submit_for_review(task_input)

            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full" if len(content_types) > 1 else content_types[0],
                npc_configs=self.generated_npcs,
                quest_configs=self.generated_quests,
                region_configs=self.generated_regions,
                event_configs=self.generated_events,
                content_package=self.content_package,
                review_request=self.review_request,
                status="completed",
            )

        except MissingSkeletonError as e:
            handle_missing_skeleton(e)
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=str(e),
            )
        except TemplateMismatchError as e:
            handle_template_mismatch(e)
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=str(e),
            )
        except ContentViolationError as e:
            handle_content_violation(e)
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=str(e),
            )
        except ReviewFailedError as e:
            handle_review_failed(e)
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=str(e),
            )
        except HighDuplicationError as e:
            handle_high_duplication(e)
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=str(e),
            )
        except Exception as e:
            return WorldGenerationResult(
                result_id=f"RESULT-{uuid4().hex[:8].upper()}",
                task_type="full",
                status="failed",
                error_message=f"Unexpected error: {str(e)}",
            )
