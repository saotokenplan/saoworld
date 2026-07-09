from app.core.quality_scorer import QualityScorer, QualityScoreResult


class TestQualityScorer:
    def test_score_npc_valid(self):
        scorer = QualityScorer()
        payload = {
            "name": "艾瑞尔·铁盾",
            "role": "铁匠",
            "personality": "勇敢",
            "faction_id": "faction_iron_guard",
            "region_id": "region_core",
            "description": "这是一位勇敢的铁匠，在铁卫城工作多年。",
            "dialogue": "欢迎来到铁卫城，旅行者。",
        }
        result = scorer.score_npc(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_npc_missing_name(self):
        scorer = QualityScorer()
        payload = {
            "role": "铁匠",
            "description": "这是一位铁匠。",
            "dialogue": "欢迎。",
            "faction_id": "faction_iron_guard",
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert "NPC name is too short or missing" in result.reasons

    def test_score_npc_missing_description(self):
        scorer = QualityScorer()
        payload = {
            "name": "艾瑞尔",
            "role": "铁匠",
            "faction_id": "faction_iron_guard",
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert "NPC description is too short or missing" in result.reasons

    def test_score_npc_risk_keywords(self):
        scorer = QualityScorer()
        payload = {
            "name": "杀手",
            "role": "刺客",
            "faction_id": "faction_shadow",
            "description": "我会kill任何人。",
            "dialogue": "我要murder你。",
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert len(result.reasons) > 0

    def test_score_quest_valid(self):
        scorer = QualityScorer()
        payload = {
            "title": "寻找失落的宝藏",
            "type": "side",
            "region_id": "region_core",
            "description": "在铁卫城周边寻找传说中的宝藏。",
            "objectives": ["前往目标地点", "击败敌人", "收集物品"],
            "rewards": {"experience": 100, "gold": 50},
        }
        result = scorer.score_quest(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_quest_missing_objectives(self):
        scorer = QualityScorer()
        payload = {
            "title": "测试任务",
            "description": "测试描述。",
            "rewards": {"experience": 100},
        }
        result = scorer.score_quest(payload)
        assert not result.is_acceptable()
        assert "Quest objectives are missing or invalid" in result.reasons

    def test_score_quest_negative_rewards(self):
        scorer = QualityScorer()
        payload = {
            "title": "测试任务",
            "description": "测试描述。",
            "objectives": ["测试"],
            "rewards": {"experience": -100, "gold": -50},
        }
        result = scorer.score_quest(payload)
        assert not result.is_acceptable()
        assert "Negative reward values" in result.reasons

    def test_score_region_valid(self):
        scorer = QualityScorer()
        payload = {
            "name": "迷雾森林",
            "difficulty": "normal",
            "region_id": "region_forest",
            "chapter_id": "chapter_01",
            "description": "一片神秘的森林，充满危险和机遇。",
            "features": ["神秘遗迹", "危险生物", "宝藏"],
        }
        result = scorer.score_region(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_region_invalid_difficulty(self):
        scorer = QualityScorer()
        payload = {
            "name": "测试区域",
            "difficulty": "super_hard",
            "description": "测试描述。",
            "features": ["测试"],
        }
        result = scorer.score_region(payload)
        assert not result.is_acceptable()
        assert any("Invalid difficulty" in r for r in result.reasons)

    def test_score_generic(self):
        scorer = QualityScorer()
        payload = {"key": "value", "data": "test data", "description": "This is a longer payload that should pass quality check"}
        result = scorer.score_generic(payload)
        assert result.is_acceptable()

        small_payload = {"a": "b"}
        result = scorer.score_generic(small_payload)
        assert not result.is_acceptable()

    def test_score_method_dispatch(self):
        scorer = QualityScorer()

        npc_result = scorer.score("npc", {"name": "Test", "description": "Test", "dialogue": "Test", "faction_id": "f1"})
        assert isinstance(npc_result, QualityScoreResult)

        quest_result = scorer.score("quest", {"title": "Test", "description": "Test", "objectives": ["Test"], "rewards": {}})
        assert isinstance(quest_result, QualityScoreResult)

        region_result = scorer.score("region", {"name": "Test", "description": "Test", "difficulty": "normal", "features": ["Test"]})
        assert isinstance(region_result, QualityScoreResult)

        generic_result = scorer.score("unknown", {"key": "value"})
        assert isinstance(generic_result, QualityScoreResult)
