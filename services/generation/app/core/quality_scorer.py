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
        valid_roles = [
            "blacksmith", "merchant", "guard", "healer", "quest_giver",
            "leader", "researcher", "farmer", "scavenger",
        ]
        if role and role not in valid_roles:
            score -= 0.03
            reasons.append(f"Role '{role}' is not in valid roles list")

        return QualityScoreResult(max(0.0, min(1.0, score)), reasons)

    def score_quest(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        required_fields = [
            "quest_key", "title", "description", "quest_type",
            "chapter_id", "region_key", "objectives",
        ]

        for field in required_fields:
            value = payload.get(field)
            if value is None:
                score -= 0.05
                reasons.append(f"Missing field: {field}")
            elif isinstance(value, str) and not value.strip():
                score -= 0.03
                reasons.append(f"Empty field: {field}")
            elif isinstance(value, list) and len(value) == 0:
                score -= 0.05
                reasons.append(f"Empty list: {field}")

        title = payload.get("title", "")
        if len(title) < 5:
            score -= 0.1
            reasons.append("Quest title is too short")
        elif len(title) > 100:
            score -= 0.05
            reasons.append("Quest title is too long")

        description = payload.get("description", "")
        if len(description) < 50:
            score -= 0.15
            reasons.append("Quest description is too short")
        elif len(description) > 500:
            score -= 0.05
            reasons.append("Quest description is too long")

        quest_type = payload.get("quest_type", "")
        valid_types = {"main", "side", "event", "daily"}
        if quest_type and quest_type not in valid_types:
            score -= 0.05
            reasons.append(f"Invalid quest type: {quest_type}")

        objectives = payload.get("objectives", [])
        if isinstance(objectives, list):
            if len(objectives) < 2:
                score -= 0.15
                reasons.append(f"Quest needs at least 2 objectives (has {len(objectives)})")
            elif len(objectives) > 10:
                score -= 0.05
                reasons.append("Too many objectives")

            for idx, obj in enumerate(objectives):
                if not isinstance(obj, dict):
                    score -= 0.03
                    reasons.append(f"Objective {idx} is not a dictionary")
                    continue
                obj_id = obj.get("id")
                obj_desc = obj.get("description", "")
                obj_type = obj.get("type", "")
                if not obj_id:
                    score -= 0.02
                    reasons.append(f"Objective {idx} missing id")
                if len(obj_desc) < 10:
                    score -= 0.02
                    reasons.append(f"Objective {idx} description is too short")
                if obj_type and obj_type not in {
                    "story", "location", "npc", "combat", "explore",
                    "collect", "rescue", "travel", "quest",
                }:
                    score -= 0.02
                    reasons.append(f"Objective {idx} has invalid type: {obj_type}")
        else:
            score -= 0.3
            reasons.append("Quest objectives must be a list")

        rewards = payload.get("rewards", {})
        if isinstance(rewards, dict):
            experience = rewards.get("experience", 0)
            gold = rewards.get("gold", 0)

            if isinstance(experience, (int, float)) and experience < 0:
                score -= 0.1
                reasons.append("Negative experience reward")
            if isinstance(gold, (int, float)) and gold < 0:
                score -= 0.1
                reasons.append("Negative gold reward")

            quest_type = payload.get("quest_type", "side")
            exp_limits = {"main": (300, 2000), "side": (50, 500), "event": (100, 800), "daily": (20, 200)}
            gold_limits = {"main": (50, 500), "side": (10, 150), "event": (30, 250), "daily": (5, 50)}

            if quest_type in exp_limits:
                min_exp, max_exp = exp_limits[quest_type]
                if isinstance(experience, (int, float)):
                    if experience < min_exp:
                        score -= 0.05
                        reasons.append(f"Experience below {quest_type} minimum ({min_exp})")
                    elif experience > max_exp:
                        score -= 0.05
                        reasons.append(f"Experience above {quest_type} maximum ({max_exp})")

                min_gold, max_gold = gold_limits[quest_type]
                if isinstance(gold, (int, float)):
                    if gold < min_gold:
                        score -= 0.03
                        reasons.append(f"Gold below {quest_type} minimum ({min_gold})")
                    elif gold > max_gold:
                        score -= 0.03
                        reasons.append(f"Gold above {quest_type} maximum ({max_gold})")
        else:
            score -= 0.15
            reasons.append("Quest rewards must be a dictionary")

        quest_key = payload.get("quest_key", "")
        if quest_key and not quest_key.startswith("quest_"):
            score -= 0.03
            reasons.append("Quest key should start with 'quest_'")

        region_key = payload.get("region_key", "")
        if region_key and not region_key.startswith("region_"):
            score -= 0.02
            reasons.append("Region key should start with 'region_'")

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

    def score_settlement(self, payload: dict[str, Any]) -> QualityScoreResult:
        reasons: list[str] = []
        score = 1.0

        required_fields = [
            "settlement_key", "name", "settlement_type",
            "region_key", "chapter_id", "description",
            "population", "main_resources", "economy_type", "status",
        ]

        for field in required_fields:
            value = payload.get(field)
            if value is None:
                score -= 0.04
                reasons.append(f"Missing field: {field}")
            elif isinstance(value, str) and not value.strip():
                score -= 0.03
                reasons.append(f"Empty field: {field}")
            elif isinstance(value, list) and len(value) == 0:
                score -= 0.04
                reasons.append(f"Empty list: {field}")
            elif isinstance(value, int) and value <= 0:
                score -= 0.04
                reasons.append(f"Invalid value for {field}: must be > 0")

        name = payload.get("name", "")
        if len(name) < 3:
            score -= 0.1
            reasons.append("Settlement name is too short")
        elif len(name) > 100:
            score -= 0.05
            reasons.append("Settlement name is too long")

        description = payload.get("description", "")
        if len(description) < 50:
            score -= 0.15
            reasons.append("Settlement description is too short")
        elif len(description) > 500:
            score -= 0.05
            reasons.append("Settlement description is too long")

        settlement_type = payload.get("settlement_type", "")
        valid_types = {"village", "town", "city", "camp", "fortress", "market", "outpost"}
        if settlement_type and settlement_type not in valid_types:
            score -= 0.05
            reasons.append(f"Invalid settlement type: {settlement_type}")

        economy_type = payload.get("economy_type", "")
        valid_economy = {"agriculture", "commerce", "mining", "hunting", "fishing", "trade"}
        if economy_type and economy_type not in valid_economy:
            score -= 0.05
            reasons.append(f"Invalid economy type: {economy_type}")

        status = payload.get("status", "")
        valid_statuses = {"peaceful", "troubled", "warring", "thriving"}
        if status and status not in valid_statuses:
            score -= 0.05
            reasons.append(f"Invalid status: {status}")

        population = payload.get("population", 0)
        if isinstance(population, (int, float)):
            settlement_type = payload.get("settlement_type", "village")
            pop_limits = {
                "village": (10, 500),
                "town": (500, 2000),
                "city": (2000, 10000),
                "camp": (5, 200),
                "fortress": (50, 500),
                "market": (100, 1000),
                "outpost": (10, 100),
            }
            if settlement_type in pop_limits:
                min_pop, max_pop = pop_limits[settlement_type]
                if population < min_pop:
                    score -= 0.05
                    reasons.append(f"Population below {settlement_type} minimum ({min_pop})")
                elif population > max_pop:
                    score -= 0.05
                    reasons.append(f"Population above {settlement_type} maximum ({max_pop})")

        main_resources = payload.get("main_resources", [])
        if isinstance(main_resources, list):
            if len(main_resources) < 1:
                score -= 0.08
                reasons.append("Settlement needs at least 1 main resource")
            elif len(main_resources) > 5:
                score -= 0.03
                reasons.append("Too many main resources (max 5)")
        else:
            score -= 0.15
            reasons.append("Main resources must be a list")

        history = payload.get("history", "")
        if len(history) < 50:
            score -= 0.08
            reasons.append("Settlement history is too short")

        settlement_key = payload.get("settlement_key", "")
        if settlement_key and not settlement_key.startswith("settlement_"):
            score -= 0.03
            reasons.append("Settlement key should start with 'settlement_'")

        region_key = payload.get("region_key", "")
        if region_key and not region_key.startswith("region_"):
            score -= 0.02
            reasons.append("Region key should start with 'region_'")

        faction_key = payload.get("faction_key", "")
        if faction_key and not faction_key.startswith("faction_"):
            score -= 0.02
            reasons.append("Faction key should start with 'faction_'")

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
            case "settlement":
                return self.score_settlement(payload)
            case _:
                return self.score_generic(payload)


quality_scorer = QualityScorer()
