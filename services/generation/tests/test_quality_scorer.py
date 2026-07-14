from app.core.quality_scorer import QualityScorer, QualityScoreResult


class TestQualityScorer:
    def test_score_npc_valid(self):
        scorer = QualityScorer()
        payload = {
            "npc_key": "npc_iron_shield",
            "name": "艾瑞尔·铁盾",
            "title": "首席铁匠",
            "gender": "male",
            "age": 45,
            "race": "human",
            "faction_key": "faction_iron_guard",
            "region_key": "region_core",
            "role": "blacksmith",
            "location_key": "loc_forge",
            "description": (
                "这是一位勇敢的铁匠，在铁卫城工作多年，为冒险者打造各种精良的武器和护甲。"
                "他技艺精湛，为人正直，深受城中居民的尊敬。"
            ),
            "personality": ["勇敢", "正直", "热情"],
            "traits": ["强壮", "专注"],
            "voice": "洪亮有力",
            "backstory": (
                "艾瑞尔·铁盾出生在铁匠世家，从小就跟随父亲学习锻造技艺。"
                "他年轻时曾参与多次战斗，见证了许多冒险者用他打造的武器战胜强敌。"
                "如今他在铁卫城开设了自己的铁匠铺，继续为新一代冒险者提供装备支持。"
            ),
            "motivation": "为冒险者打造最强武器",
            "relationship_map": {},
            "dialog_style": "热情豪爽",
            "dialog_nodes": {
                "first_meet": {
                    "id": "first_meet", "text": "欢迎来到铁卫城，旅行者。需要武器吗？",
                    "speaker": "npc", "choices": [],
                },
                "about_work": {
                    "id": "about_work", "text": "我在这里锻造了二十年，每件作品都是我的心血。",
                    "speaker": "npc", "choices": [],
                },
                "has_quest": {"id": "has_quest", "text": "我需要一些稀有材料。", "speaker": "npc", "choices": []},
                "quest_accepted": {"id": "quest_accepted", "text": "太好了，谢谢你！", "speaker": "npc", "choices": []},
                "quest_completed": {
                    "id": "quest_completed", "text": "完美！这正是我需要的。",
                    "speaker": "npc", "choices": [],
                },
                "default": {"id": "default", "text": "有什么需要帮助的吗？", "speaker": "npc", "choices": []},
                "goodbye": {"id": "goodbye", "text": "", "speaker": "npc", "choices": [], "is_end": True},
            },
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 100,
            "location_y": 200,
            "interaction_radius": 30,
        }
        result = scorer.score_npc(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_npc_missing_name(self):
        scorer = QualityScorer()
        payload = {
            "npc_key": "npc_test",
            "role": "blacksmith",
            "description": "这是一位铁匠。",
            "faction_key": "faction_iron_guard",
            "region_key": "region_core",
            "location_key": "loc_test",
            "personality": ["brave"],
            "traits": ["strong"],
            "voice": "deep",
            "backstory": "Test backstory.",
            "motivation": "Test motivation.",
            "relationship_map": {},
            "dialog_style": "test",
            "dialog_nodes": {},
            "title": "",
            "gender": "",
            "age": 0,
            "race": "",
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert "Missing field: name" in result.reasons

    def test_score_npc_missing_description(self):
        scorer = QualityScorer()
        payload = {
            "npc_key": "npc_test",
            "name": "艾瑞尔",
            "role": "blacksmith",
            "faction_key": "faction_iron_guard",
            "region_key": "region_core",
            "location_key": "loc_test",
            "personality": ["brave"],
            "traits": ["strong"],
            "voice": "deep",
            "backstory": "Test backstory.",
            "motivation": "Test motivation.",
            "relationship_map": {},
            "dialog_style": "test",
            "dialog_nodes": {},
            "title": "",
            "gender": "",
            "age": 0,
            "race": "",
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert "Empty field: description" in result.reasons or "Missing field: description" in result.reasons

    def test_score_npc_risk_keywords(self):
        scorer = QualityScorer()
        payload = {
            "npc_key": "npc_killer",
            "name": "杀手",
            "title": "",
            "gender": "male",
            "age": 30,
            "race": "human",
            "faction_key": "faction_shadow",
            "region_key": "region_core",
            "role": "assassin",
            "location_key": "loc_shadow",
            "description": "我会kill任何人。",
            "personality": ["cruel"],
            "traits": ["stealthy"],
            "voice": "whisper",
            "backstory": "我要murder所有人。",
            "motivation": "To kill.",
            "relationship_map": {},
            "dialog_style": "sinister",
            "dialog_nodes": {},
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
        }
        result = scorer.score_npc(payload)
        assert not result.is_acceptable()
        assert len(result.reasons) > 0

    def test_score_quest_valid(self):
        scorer = QualityScorer()
        payload = {
            "quest_key": "quest_treasure_hunt_01",
            "quest_type": "side",
            "title": "寻找失落的宝藏",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
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
            "quest_key": "quest_test_01",
            "quest_type": "side",
            "title": "测试任务",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "rewards": {"experience": 100},
        }
        result = scorer.score_quest(payload)
        assert not result.is_acceptable()
        assert any("objectives" in r.lower() for r in result.reasons)

    def test_score_quest_negative_rewards(self):
        scorer = QualityScorer()
        payload = {
            "quest_key": "quest_test_02",
            "quest_type": "side",
            "title": "测试任务",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "objectives": ["测试"],
            "rewards": {"experience": -100, "gold": -50},
        }
        result = scorer.score_quest(payload)
        assert not result.is_acceptable()
        assert any("reward" in r.lower() or "negative" in r.lower() for r in result.reasons)

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
        payload = {
            "key": "value", "data": "test data",
            "description": "This is a longer payload that should pass quality check",
        }
        result = scorer.score_generic(payload)
        assert result.is_acceptable()

        small_payload = {"a": "b"}
        result = scorer.score_generic(small_payload)
        assert not result.is_acceptable()

    def test_score_settlement_valid(self):
        scorer = QualityScorer()
        payload = {
            "settlement_key": "settlement_village_test",
            "name": "晨光村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "一座宁静的小村庄，以农业为主，村民们和睦相处，过着自给自足的生活。",
            "population": 200,
            "main_resources": ["谷物", "木材"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [
                {"location_key": "loc_center", "name": "广场", "description": "村庄中心广场"},
            ],
            "key_npcs": ["npc_leader_01"],
            "faction_influence": {"faction_iron_guard": "主导"},
            "relationships": {},
            "history": "晨光村建于数百年前，由一群逃难的农民建立。",
            "culture": "民风淳朴，重视传统和家庭。",
            "defenses": ["木墙"],
            "services": ["旅馆", "商店"],
            "special_features": ["每周市集"],
            "location_x": 100,
            "location_y": 200,
        }
        result = scorer.score_settlement(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_settlement_missing_required_fields(self):
        scorer = QualityScorer()
        payload = {
            "settlement_key": "settlement_test",
            "name": "测试村",
        }
        result = scorer.score_settlement(payload)
        assert not result.is_acceptable()
        assert len(result.reasons) > 0

    def test_score_settlement_invalid_type(self):
        scorer = QualityScorer()
        payload = {
            "settlement_key": "settlement_test",
            "name": "测试村",
            "settlement_type": "invalid_type",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "population": 100,
            "main_resources": ["资源1"],
            "economy_type": "agriculture",
            "status": "peaceful",
        }
        result = scorer.score_settlement(payload)
        assert any("Invalid settlement type" in r for r in result.reasons)

    def test_score_settlement_population_out_of_range(self):
        scorer = QualityScorer()
        payload = {
            "settlement_key": "settlement_test",
            "name": "测试村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "description": "测试描述。",
            "population": 10000,
            "main_resources": ["资源1"],
            "economy_type": "agriculture",
            "status": "peaceful",
        }
        result = scorer.score_settlement(payload)
        assert any("Population above village maximum" in r for r in result.reasons)

    def test_score_method_dispatch(self):
        scorer = QualityScorer()

        npc_result = scorer.score(
            "npc", {"name": "Test", "description": "Test", "dialogue": "Test", "faction_id": "f1"}
        )
        assert isinstance(npc_result, QualityScoreResult)

        quest_result = scorer.score(
            "quest", {"title": "Test", "description": "Test", "objectives": ["Test"], "rewards": {}}
        )
        assert isinstance(quest_result, QualityScoreResult)

        region_result = scorer.score(
            "region", {"name": "Test", "description": "Test", "difficulty": "normal", "features": ["Test"]}
        )
        assert isinstance(region_result, QualityScoreResult)

        settlement_result = scorer.score(
            "settlement", {
                "settlement_key": "settlement_test", "name": "Test",
                "settlement_type": "village", "region_key": "region_core",
                "chapter_id": "chapter_01", "description": "Test", "population": 100,
                "main_resources": ["Test"], "economy_type": "agriculture", "status": "peaceful",
            }
        )
        assert isinstance(settlement_result, QualityScoreResult)

        generic_result = scorer.score("unknown", {"key": "value"})
        assert isinstance(generic_result, QualityScoreResult)

    def test_score_boss_valid(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_ancient_tree",
            "name": "古树守护者",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "region_key": "region_forest_01",
            "level": 12,
            "hp": 800,
            "attack": 28,
            "defense": 15,
            "speed": 3,
            "description": "幽光森林深处的千年古树，被自然之力赋予了意识。它守护着森林的秘密，任何闯入者都会遭受到它的愤怒攻击。古树拥有多个战斗阶段，随着战斗的进行会释放更强大的技能。",
            "behavior_pattern": {
                "aggression": "aggressive",
                "attack_pattern": "magic",
                "special_behaviors": ["enrage", "phase_change"],
            },
            "loot_table": [
                {"item_key": "item_ancient_core", "drop_rate": 1.0, "quantity_min": 1, "quantity_max": 1},
            ],
            "skills": [
                {"skill_key": "skill_root_strike", "name": "根系打击", "damage_multiplier": 1.0, "cooldown": 0},
                {"skill_key": "skill_vine_whip", "name": "藤蔓鞭打", "damage_multiplier": 1.5, "cooldown": 3},
            ],
            "is_boss": True,
            "boss_rank": "legendary",
            "phase_count": 3,
            "special_skills": [
                {"skill_key": "skill_root_bind", "name": "根系缠绕", "description": "束缚玩家", "cooldown": 8},
                {"skill_key": "skill_nature_force", "name": "自然之力", "description": "恢复生命", "cooldown": 15},
                {"skill_key": "skill_ancient_rage", "name": "古树之怒", "description": "全屏攻击", "cooldown": 20},
            ],
            "enrage_threshold": 0.3,
            "reward": {
                "experience": 5000,
                "items": [{"item_key": "item_ancient_core", "quantity": 1}],
            },
        }
        result = scorer.score_boss(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_boss_missing_boss_fields(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_test",
            "name": "测试Boss",
            "monster_type": "boss",
            "chapter_id": "chapter_02",
            "level": 10,
            "hp": 500,
            "attack": 25,
            "defense": 10,
            "speed": 4,
            "description": "测试描述。",
        }
        result = scorer.score_boss(payload)
        assert not result.is_acceptable()
        assert len(result.reasons) > 0

    def test_score_boss_invalid_boss_rank(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_test",
            "name": "测试Boss",
            "monster_type": "boss",
            "boss_rank": "invalid",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        }
        result = scorer.score_boss(payload)
        assert any("Invalid boss rank" in r for r in result.reasons)

    def test_score_boss_phase_count_zero(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_test",
            "name": "测试Boss",
            "monster_type": "boss",
            "boss_rank": "legendary",
            "phase_count": 0,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        }
        result = scorer.score_boss(payload)
        assert any("Boss must have at least 1 phase" in r for r in result.reasons)

    def test_score_boss_enrage_threshold_out_of_range(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_test",
            "name": "测试Boss",
            "monster_type": "boss",
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 1.5,
            "reward": {"experience": 3000, "items": []},
        }
        result = scorer.score_boss(payload)
        assert any("Enrage threshold must be between 0 and 1" in r for r in result.reasons)

    def test_score_boss_dispatch(self):
        scorer = QualityScorer()
        payload = {
            "monster_key": "boss_test",
            "name": "测试Boss",
            "monster_type": "boss",
            "boss_rank": "legendary",
            "phase_count": 2,
            "special_skills": [],
            "enrage_threshold": 0.3,
            "reward": {"experience": 3000, "items": []},
        }
        result = scorer.score("boss", payload)
        assert isinstance(result, QualityScoreResult)

    def test_score_item_valid(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_sword_steel",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "钢铁长剑",
            "description": "一把普通的钢铁长剑，适合新手使用。",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "stats": {"attack": 10, "speed": 5},
            "effects": {"effect_type": "passive", "description": "普通攻击"},
            "sell_price": 50,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert result.is_acceptable()
        assert result.score >= 0.75

    def test_score_item_missing_required_fields(self):
        scorer = QualityScorer()
        payload = {"name": "测试装备"}
        result = scorer.score_item(payload)
        assert not result.is_acceptable()
        assert len(result.reasons) > 0
        assert any("item_key" in r.lower() for r in result.reasons)
        assert any("item_type" in r.lower() for r in result.reasons)

    def test_score_item_invalid_type(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "invalid_type",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Invalid item type" in r for r in result.reasons)

    def test_score_item_invalid_rarity(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "invalid",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Invalid rarity" in r for r in result.reasons)

    def test_score_item_level_out_of_range(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 100,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Level requirement out of range" in r for r in result.reasons)

    def test_score_item_negative_sell_price(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": -10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Sell price must be non-negative" in r for r in result.reasons)

    def test_score_item_weapon_stackable(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": True,
        }
        result = scorer.score_item(payload)
        assert any("weapon items should not be stackable" in r.lower() for r in result.reasons)

    def test_score_item_consumable_not_stackable(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "consumable",
            "name": "测试药水",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("consumable items should be stackable" in r.lower() for r in result.reasons)

    def test_score_item_negative_stats(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "stats": {"attack": -5},
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("attack" in r.lower() and "negative" in r.lower() for r in result.reasons)

    def test_score_item_invalid_effect_type(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "effects": {"effect_type": "invalid"},
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Invalid effect type" in r for r in result.reasons)

    def test_score_item_invalid_key_prefix(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "sword_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score_item(payload)
        assert any("Item key should start with" in r for r in result.reasons)

    def test_score_item_dispatch(self):
        scorer = QualityScorer()
        payload = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "测试装备",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }
        result = scorer.score("item", payload)
        assert isinstance(result, QualityScoreResult)
