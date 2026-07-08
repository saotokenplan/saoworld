from enum import Enum
from typing import Any


class RequirementStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RequirementPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TargetScope(str, Enum):
    CONTENT = "content"
    GAMEPLAY = "gameplay"
    SYSTEM = "system"
    WORLD = "world"


PRIORITY_MAP: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def generate_requirements_from_insight(insight_data: dict[str, Any]) -> list[dict]:
    requirements = []

    category = insight_data.get("category")
    summary = insight_data.get("summary", "")
    confidence = insight_data.get("confidence", "medium")
    impact = insight_data.get("impact", "medium")
    feasibility = insight_data.get("feasibility", "medium")

    priority = _determine_priority(confidence, impact)
    target_scope = _determine_scope(category)

    if category == "region_heat":
        requirements.extend(_generate_region_heat_requirements(summary, insight_data))
    elif category == "content_gap":
        requirements.extend(_generate_content_gap_requirements(summary, insight_data))
    elif category == "difficulty_feedback":
        requirements.extend(_generate_difficulty_requirements(summary, insight_data))
    elif category == "content_preference":
        requirements.extend(_generate_preference_requirements(summary, insight_data))
    elif category == "vote_preference":
        requirements.extend(_generate_vote_requirements(summary, insight_data))
    else:
        requirements.append(_generate_generic_requirement(summary, insight_data))

    for req in requirements:
        req["priority"] = priority
        req["target_scope"] = target_scope
        req["estimated_effort"] = _estimate_effort(feasibility, target_scope)

    return requirements


def _determine_priority(confidence: str, impact: str) -> str:
    conf_score = PRIORITY_MAP.get(confidence, 2)
    imp_score = PRIORITY_MAP.get(impact, 2)

    avg_score = (conf_score + imp_score) / 2

    if avg_score >= 3:
        return RequirementPriority.HIGH.value
    elif avg_score >= 2:
        return RequirementPriority.MEDIUM.value
    else:
        return RequirementPriority.LOW.value


def _determine_scope(category: str) -> str:
    scope_map = {
        "region_heat": TargetScope.WORLD.value,
        "content_gap": TargetScope.CONTENT.value,
        "difficulty_feedback": TargetScope.GAMEPLAY.value,
        "content_preference": TargetScope.CONTENT.value,
        "vote_preference": TargetScope.CONTENT.value,
        "player_behavior": TargetScope.GAMEPLAY.value,
        "system_health": TargetScope.SYSTEM.value,
    }
    return scope_map.get(category, TargetScope.CONTENT.value)


def _estimate_effort(feasibility: str, target_scope: str) -> int:
    effort = 1

    if feasibility == "low":
        effort += 2
    elif feasibility == "high":
        effort -= 0

    if target_scope == "system":
        effort += 1
    elif target_scope == "world":
        effort += 1

    return max(1, effort)


def _generate_region_heat_requirements(summary: str, insight_data: dict) -> list[dict]:
    source_data = insight_data.get("source_data_jsonb", {})
    region_id = source_data.get("region_id", "")

    return [
        {
            "title": f"扩展热门区域 {region_id} 内容",
            "description": f"根据数据分析，区域 {region_id} 访问量显著高于平均水平。建议在该区域增加更多支线任务、NPC互动和探索点，以满足玩家需求。",
            "acceptance_criteria_jsonb": {
                "新增支线任务数量": 3,
                "新增NPC数量": 2,
                "新增探索点数量": 5,
                "区域内容包版本": "pkg_xxx",
            },
            "related_content_jsonb": {
                "region_id": region_id,
                "content_type": ["quest", "npc", "exploration"],
            },
        }
    ]


def _generate_content_gap_requirements(summary: str, insight_data: dict) -> list[dict]:
    source_data = insight_data.get("source_data_jsonb", {})
    region_id = source_data.get("region_id", "")

    return [
        {
            "title": f"填充区域 {region_id} 内容缺口",
            "description": f"根据数据分析，区域 {region_id} 访问量显著低于平均水平，可能存在内容缺口。建议分析该区域现有内容，增加吸引玩家的任务和活动。",
            "acceptance_criteria_jsonb": {
                "内容缺口分析报告": "completed",
                "新增任务数量": 2,
                "区域改进方案": "approved",
            },
            "related_content_jsonb": {
                "region_id": region_id,
                "content_type": ["analysis", "quest", "event"],
            },
        }
    ]


def _generate_difficulty_requirements(summary: str, insight_data: dict) -> list[dict]:
    source_data = insight_data.get("source_data_jsonb", {})
    quest_id = source_data.get("quest_id", "")
    completion_rate = source_data.get("completion_rate", 0)

    if completion_rate < 0.3:
        return [
            {
                "title": f"调整任务 {quest_id} 难度",
                "description": f"任务 {quest_id} 完成率较低({completion_rate:.1%})，玩家反馈难度偏高。建议降低敌人强度、增加引导提示或提供难度选择。",
                "acceptance_criteria_jsonb": {
                    "任务难度评估": "completed",
                    "难度调整方案": "approved",
                    "调整后完成率目标": "> 50%",
                },
                "related_content_jsonb": {
                    "quest_id": quest_id,
                    "content_type": ["balance", "tuning"],
                },
            }
        ]
    else:
        return [
            {
                "title": f"增加任务 {quest_id} 挑战性",
                "description": f"任务 {quest_id} 完成率很高且用时短，玩家反馈难度偏低。建议增加敌人强度或添加额外挑战目标。",
                "acceptance_criteria_jsonb": {
                    "任务难度评估": "completed",
                    "难度提升方案": "approved",
                    "调整后完成率目标": "< 90%",
                },
                "related_content_jsonb": {
                    "quest_id": quest_id,
                    "content_type": ["balance", "challenge"],
                },
            }
        ]


def _generate_preference_requirements(summary: str, insight_data: dict) -> list[dict]:
    source_data = insight_data.get("source_data_jsonb", {})

    if "exploration" in summary:
        return [
            {
                "title": "增加探索型内容",
                "description": "数据分析显示玩家更倾向于探索行为。建议在世界中增加更多隐藏区域、秘密宝藏和探索型支线任务。",
                "acceptance_criteria_jsonb": {
                    "新增隐藏区域数量": 2,
                    "新增探索型支线": 3,
                    "新增宝藏数量": 5,
                },
                "related_content_jsonb": {
                    "content_type": ["exploration", "secret", "treasure"],
                },
            }
        ]
    elif "NPC" in summary:
        return [
            {
                "title": "增加NPC互动内容",
                "description": "数据分析显示玩家更倾向于与NPC互动。建议增加更多NPC对话选项、支线任务和好感度系统。",
                "acceptance_criteria_jsonb": {
                    "新增NPC数量": 3,
                    "新增对话分支": 10,
                    "NPC好感度系统": "design",
                },
                "related_content_jsonb": {
                    "content_type": ["npc", "dialogue", "relationship"],
                },
            }
        ]
    else:
        return _generate_generic_requirement(summary, insight_data)


def _generate_vote_requirements(summary: str, insight_data: dict) -> list[dict]:
    source_data = insight_data.get("source_data_jsonb", {})
    cycle_id = source_data.get("cycle_id", "")
    winner = source_data.get("winner", "")

    return [
        {
            "title": f"实现投票结果 {winner} 的内容落地",
            "description": f"投票周期 {cycle_id} 中候选项 {winner} 获得压倒性支持。建议根据该选项生成对应的游戏内容更新，包括新区域、新任务或世界变化。",
            "acceptance_criteria_jsonb": {
                "内容方案设计": "approved",
                "内容包开发": "completed",
                "灰度发布": "scheduled",
            },
            "related_content_jsonb": {
                "vote_cycle_id": cycle_id,
                "winning_candidate": winner,
                "content_type": ["content_package", "world_update"],
            },
        }
    ]


def _generate_generic_requirement(summary: str, insight_data: dict) -> list[dict]:
    return [
        {
            "title": f"处理洞察：{summary[:50]}...",
            "description": f"根据数据分析洞察：{summary}。建议运营人员审核并确定具体的内容或系统改进方案。",
            "acceptance_criteria_jsonb": {
                "运营审核": "pending",
                "改进方案": "pending",
            },
            "related_content_jsonb": {
                "insight_summary": summary,
                "content_type": ["review"],
            },
        }
    ]