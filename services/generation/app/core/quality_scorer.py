import json
from typing import Any

from app.core.config import settings


class QualityScoreResult:
    def __init__(self, score: float, reasons: list[str]):
        self.score = score
        self.reasons = reasons

    def is_acceptable(self) -> bool:
        return self.score >= settings.quality_threshold


class QualityScorer:
    def __init__(self, threshold: float | None = None):
        self.threshold = threshold or settings.quality_threshold

    def score_npc(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        required_fields = [
            "npc_key", "name", "title", "gender", "age", "race",
            "faction_key", "region_key", "role", "location_key",
            "description", "personality", "traits", "voice",
            "backstory", "motivation", "dialog_style", "dialog_nodes",
        ]

        for field in required_fields:
            value = payload.get(field)
            if value is None:
                score -= 0.03
                reasons.append(f"Missing field: {field}")
            elif isinstance(value, str) and not value.strip():
                score -= 0.02
                reasons.append(f"Empty field: {field}")

        name = payload.get("name", "")
        if len(name) < 2:
            score -= 0.05
            reasons.append("NPC name is too short")
        elif len(name) > 50:
            score -= 0.02
            reasons.append("NPC name is too long")

        description = payload.get("description", "")
        if len(description) < 50:
            score -= 0.1
            reasons.append("NPC description is too short")
        elif len(description) > 500:
            score -= 0.03
            reasons.append("NPC description is too long")

        backstory = payload.get("backstory", "")
        if len(backstory) < 100:
            score -= 0.08
            reasons.append("NPC backstory is too short")

        personality = payload.get("personality", [])
        if not isinstance(personality, list) or len(personality) < 2:
            score -= 0.05
            reasons.append("NPC personality needs at least 2 traits")

        dialog_nodes = payload.get("dialog_nodes", {})
        if isinstance(dialog_nodes, dict):
            node_count = len(dialog_nodes)
            if node_count < 6:
                score -= 0.1
                reasons.append(f"Dialog tree needs at least 6 nodes (has {node_count})")
        else:
            score -= 0.15
            reasons.append("Dialog nodes must be a dictionary")

        risk_keywords = ["kill", "murder", "death", "destroy", "suicide", "terrorist"]
        text_content = f"{description} {backstory}"
        for keyword in risk_keywords:
            if keyword.lower() in text_content.lower():
                score -= 0.2
                reasons.append(f"Contains risk keyword: {keyword}")

        faction_key = payload.get("faction_key", "")
        if faction_key and not faction_key.startswith("faction_"):
            score -= 0.02
            reasons.append("Faction key should start with 'faction_'")

        role = payload.get("role", "")
        valid_roles = ["blacksmith", "merchant", "guard", "healer", "quest_giver", "leader", "researcher", "farmer", "scavenger"]
        if role and role not in valid_roles:
            score -= 0.03
            reasons.append(f"Role '{role}' is not in valid roles list")

        return QualityScoreResult(max(0.0, min(1.0, score)), reasons)

    def score_quest(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        title = payload.get("title", "")
        description = payload.get("description", "")
        objectives = payload.get("objectives", [])
        rewards = payload.get("rewards", {})

        if not title or len(title) < 5:
            score -= 0.2
            reasons.append("Quest title is too short or missing")
        elif len(title) > 100:
            score -= 0.1
            reasons.append("Quest title is too long")

        if not description or len(description) < 30:
            score -= 0.25
            reasons.append("Quest description is too short or missing")

        if not isinstance(objectives, list) or len(objectives) == 0:
            score -= 0.3
            reasons.append("Quest objectives are missing or invalid")
        elif len(objectives) > 10:
            score -= 0.1
            reasons.append("Too many objectives")

        if not isinstance(rewards, dict):
            score -= 0.15
            reasons.append("Quest rewards are invalid")

        reward_values = []
        for key in ["experience", "gold", "items"]:
            if key in rewards:
                reward_values.append(rewards[key])

        for val in reward_values:
            if isinstance(val, (int, float)) and val < 0:
                score -= 0.15
                reasons.append("Negative reward values")
                break

        return QualityScoreResult(max(0.0, min(1.0, score)), reasons)

    def score_region(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        name = payload.get("name", "")
        description = payload.get("description", "")
        difficulty = payload.get("difficulty", "")
        features = payload.get("features", [])

        if not name or len(name) < 3:
            score -= 0.2
            reasons.append("Region name is too short or missing")

        if not description or len(description) < 50:
            score -= 0.25
            reasons.append("Region description is too short or missing")

        valid_difficulties = ["easy", "normal", "hard", "extreme"]
        if difficulty and difficulty.lower() not in valid_difficulties:
            score -= 0.15
            reasons.append(f"Invalid difficulty: {difficulty}")

        if not isinstance(features, list) or len(features) == 0:
            score -= 0.2
            reasons.append("Region features are missing or invalid")

        return QualityScoreResult(max(0.0, min(1.0, score)), reasons)

    def score_generic(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        json_str = json.dumps(payload)
        if len(json_str) < 50:
            score -= 0.3
            reasons.append("Payload is too short")
        elif len(json_str) > 5000:
            score -= 0.15
            reasons.append("Payload is too large")

        return QualityScoreResult(max(0.0, min(1.0, score)), reasons)

    def score(self, object_type: str, payload: dict[str, Any]) -> QualityScoreResult:
        match object_type.lower():
            case "npc":
                return self.score_npc(payload)
            case "quest":
                return self.score_quest(payload)
            case "region":
                return self.score_region(payload)
            case _:
                return self.score_generic(payload)


quality_scorer = QualityScorer()