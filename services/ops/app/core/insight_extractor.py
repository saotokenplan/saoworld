from enum import Enum
from typing import Any


class InsightCategory(str, Enum):
    CONTENT_PREFERENCE = "content_preference"
    REGION_HEAT = "region_heat"
    VOTE_PREFERENCE = "vote_preference"
    DIFFICULTY_FEEDBACK = "difficulty_feedback"
    CONTENT_GAP = "content_gap"
    PLAYER_BEHAVIOR = "player_behavior"
    SYSTEM_HEALTH = "system_health"


class QualityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


QUALITY_SCORE_MAP: dict[str, float] = {
    "low": 0.33,
    "medium": 0.67,
    "high": 1.0,
}


def calculate_quality_score(
    confidence: str,
    impact: str,
    novelty: str,
    feasibility: str,
) -> float:
    score = (
        QUALITY_SCORE_MAP.get(confidence, 0.5) * 0.3 +
        QUALITY_SCORE_MAP.get(impact, 0.5) * 0.3 +
        QUALITY_SCORE_MAP.get(novelty, 0.5) * 0.2 +
        QUALITY_SCORE_MAP.get(feasibility, 0.5) * 0.2
    )
    return round(score, 2)


def extract_insights_from_report(report_data: dict[str, Any]) -> list[dict]:
    insights: list[dict] = []

    summary = report_data.get("summary_jsonb", {})
    details = report_data.get("detail_jsonb", {})

    insights.extend(_extract_region_heat_insights(summary, details))
    insights.extend(_extract_quest_difficulty_insights(summary, details))
    insights.extend(_extract_content_preference_insights(summary, details))
    insights.extend(_extract_vote_preference_insights(summary, details))

    return insights


def _extract_region_heat_insights(summary: dict, details: dict) -> list[dict]:
    insights: list[dict] = []

    regions = details.get("regions", {})
    if not regions:
        return insights

    avg_visits = sum(r.get("total_visits", 0) for r in regions.values()) / max(len(regions), 1)

    for region_id, data in regions.items():
        visits = data.get("total_visits", 0)
        if visits > avg_visits * 1.5:
            insights.append({
                "category": InsightCategory.REGION_HEAT.value,
                "summary": f"区域 {region_id} 访问量显著高于平均水平",
                "confidence": "high",
                "impact": "medium",
                "novelty": "low",
                "feasibility": "high",
                "source_data_jsonb": {"region_id": region_id, "visits": visits, "avg_visits": avg_visits},
                "tags": ["region", "popular"],
            })
        elif visits < avg_visits * 0.3:
            insights.append({
                "category": InsightCategory.CONTENT_GAP.value,
                "summary": f"区域 {region_id} 访问量显著低于平均水平，可能存在内容缺口",
                "confidence": "medium",
                "impact": "medium",
                "novelty": "medium",
                "feasibility": "medium",
                "source_data_jsonb": {"region_id": region_id, "visits": visits, "avg_visits": avg_visits},
                "tags": ["region", "content_gap"],
            })

    return insights


def _extract_quest_difficulty_insights(summary: dict, details: dict) -> list[dict]:
    insights: list[dict] = []

    quests = details.get("quests", {})
    if not quests:
        return insights

    for quest_id, data in quests.items():
        started = data.get("started_count", 0)
        completed = data.get("completed_count", 0)
        failed = data.get("failed_count", 0)
        total = started + failed

        if total > 0:
            completion_rate = completed / total
            avg_duration = data.get("avg_duration_seconds", 0)

            if completion_rate < 0.3:
                insights.append({
                    "category": InsightCategory.DIFFICULTY_FEEDBACK.value,
                    "summary": f"任务 {quest_id} 完成率较低({completion_rate:.1%})，难度可能偏高",
                    "confidence": "high",
                    "impact": "high",
                    "novelty": "low",
                    "feasibility": "high",
                    "source_data_jsonb": {"quest_id": quest_id, "completion_rate": completion_rate, "total": total},
                    "tags": ["quest", "difficulty", "high"],
                })
            elif completion_rate > 0.9 and avg_duration < 300:
                insights.append({
                    "category": InsightCategory.DIFFICULTY_FEEDBACK.value,
                    "summary": f"任务 {quest_id} 完成率很高({completion_rate:.1%})且用时短，难度可能偏低",
                    "confidence": "medium",
                    "impact": "low",
                    "novelty": "low",
                    "feasibility": "high",
                    "source_data_jsonb": {
                        "quest_id": quest_id,
                        "completion_rate": completion_rate,
                        "duration": avg_duration,
                    },
                    "tags": ["quest", "difficulty", "low"],
                })

    return insights


def _extract_content_preference_insights(summary: dict, details: dict) -> list[dict]:
    insights = []

    event_types = details.get("event_type_distribution", {})
    if event_types:
        total_events = sum(event_types.values())
        if total_events > 0:
            exploration_events = event_types.get("player.enter_region", 0) + event_types.get("player.leave_region", 0)
            interaction_events = event_types.get("player.interact_npc", 0)
            _quest_events = event_types.get("player.complete_quest", 0)

            exploration_ratio = exploration_events / total_events
            interaction_ratio = interaction_events / total_events

            if exploration_ratio > 0.4:
                insights.append({
                    "category": InsightCategory.CONTENT_PREFERENCE.value,
                    "summary": "玩家更倾向于探索行为，占比 {exploration_ratio:.1%}",
                    "confidence": "high",
                    "impact": "medium",
                    "novelty": "medium",
                    "feasibility": "medium",
                    "source_data_jsonb": {"exploration_ratio": exploration_ratio, "total_events": total_events},
                    "tags": ["player_behavior", "exploration"],
                })

            if interaction_ratio > 0.3:
                insights.append({
                    "category": InsightCategory.CONTENT_PREFERENCE.value,
                    "summary": "玩家更倾向于与NPC互动，占比 {interaction_ratio:.1%}",
                    "confidence": "high",
                    "impact": "medium",
                    "novelty": "low",
                    "feasibility": "medium",
                    "source_data_jsonb": {"interaction_ratio": interaction_ratio, "total_events": total_events},
                    "tags": ["player_behavior", "npc_interaction"],
                })

    return insights


def _extract_vote_preference_insights(summary: dict, details: dict) -> list[dict]:
    insights = []

    vote_data = details.get("vote_analysis", {})
    if vote_data:
        for cycle_id, cycle_data in vote_data.items():
            candidates = cycle_data.get("candidate_votes", {})
            if candidates:
                total_votes = sum(candidates.values())
                if total_votes > 0:
                    winner = max(candidates, key=candidates.get)
                    winner_votes = candidates[winner]
                    win_ratio = winner_votes / total_votes

                    if win_ratio > 0.6:
                        insights.append({
                            "category": InsightCategory.VOTE_PREFERENCE.value,
                            "summary": f"投票周期 {cycle_id} 中候选项 {winner} 获得压倒性支持({win_ratio:.1%})",
                            "confidence": "high",
                            "impact": "high",
                            "novelty": "medium",
                            "feasibility": "high",
                            "source_data_jsonb": {"cycle_id": cycle_id, "winner": winner, "win_ratio": win_ratio},
                            "tags": ["vote", "preference", "clear"],
                        })

    return insights
