"""内容生成器测试。"""

import pytest

from app.core.content_generator import ContentGenerator, ContentGenerationError
from app.core.llm_adapter import MockLLMAdapter
from app.core.quality_scorer import QualityScorer
from app.core.template_manager import TemplateManager


@pytest.fixture
def generator():
    """创建内容生成器实例。"""
    llm_adapter = MockLLMAdapter()
    llm_adapter.mock_response = {
        "npc_key": "npc_test",
        "name": "Test NPC",
        "title": "Test",
        "gender": "male",
        "age": 30,
        "race": "human",
        "faction_key": "faction_ironward",
        "region_key": "region_core",
        "role": "blacksmith",
        "location_key": "loc_test",
        "description": (
            "A skilled blacksmith who has worked in the forge for over 20 years. "
            "He is known for his exceptional craftsmanship and gruff but honest demeanor."
        ),
        "personality": ["gruff", "skilled", "honest"],
        "traits": ["strong", "meticulous"],
        "voice": "deep and gruff",
        "backstory": (
            "Test NPC was born into a family of skilled craftsmen. From a young age, "
            "he showed exceptional talent for working with metal, spending countless hours "
            "in the forge alongside his father."
        ),
        "motivation": "To craft the finest weapons and armor.",
        "relationship_map": {},
        "dialog_style": "direct",
        "dialog_nodes": {
            "first_meet": {"id": "first_meet", "text": "Hello!", "speaker": "npc", "choices": []},
            "about_work": {
                "id": "about_work", "text": "I've been forging for years.",
                "speaker": "npc", "choices": [],
            },
            "has_quest": {"id": "has_quest", "text": "I need materials.", "speaker": "npc", "choices": []},
            "quest_accepted": {"id": "quest_accepted", "text": "Great!", "speaker": "npc", "choices": []},
            "quest_completed": {"id": "quest_completed", "text": "Thank you!", "speaker": "npc", "choices": []},
            "default": {"id": "default", "text": "Welcome!", "speaker": "npc", "choices": []},
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
    template_manager = TemplateManager()
    quality_scorer = QualityScorer()
    return ContentGenerator(
        llm_adapter=llm_adapter,
        template_manager=template_manager,
        quality_scorer=quality_scorer,
        quality_threshold=0.75,
    )


class TestContentGenerator:
    """内容生成器测试。"""

    @pytest.mark.asyncio
    async def test_generate_npc(self, generator):
        """测试 NPC 生成。"""
        npc = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
        )

        assert isinstance(npc, dict)
        assert "name" in npc
        assert "role" in npc
        assert "description" in npc

    @pytest.mark.asyncio
    async def test_generate_npc_with_context(self, generator):
        """测试带上下文的 NPC 生成。"""
        npc = await generator.generate_npc(
            region_id="region_core",
            chapter_id="chapter_01",
            context={"faction": "faction_ironward", "role": "blacksmith"},
        )

        assert isinstance(npc, dict)
        assert "name" in npc

    @pytest.mark.asyncio
    async def test_generate_quest(self, generator):
        """测试任务生成。"""
        generator.llm_adapter.mock_response = {
            "quest_key": "quest_treasure_hunt_01",
            "quest_type": "side",
            "title": "寻找失落的宝藏",
            "region_key": "region_core",
            "region_id": "region_core",
            "chapter_id": "chapter_01",
            "description": "在铁卫城周边寻找传说中的宝藏。据说宝藏藏在一处古老的遗迹中，需要穿越重重障碍才能到达。",
            "objectives": ["前往目标地点", "击败守卫敌人", "收集宝藏物品"],
            "rewards": {"experience": 100, "gold": 50},
        }
        quest = await generator.generate_quest(
            region_id="region_core",
            chapter_id="chapter_01",
            quest_type="side",
        )

        assert isinstance(quest, dict)
        assert "title" in quest
        assert "objectives" in quest
        assert "rewards" in quest

    @pytest.mark.asyncio
    async def test_generate_quest_with_context(self, generator):
        """测试带上下文的任务生成。"""
        generator.llm_adapter.mock_response = {
            "quest_key": "quest_forest_explore_01",
            "quest_type": "side",
            "title": "森林探险之旅",
            "region_key": "region_core",
            "region_id": "region_core",
            "chapter_id": "chapter_01",
            "description": "探索迷雾森林，发现隐藏的秘密。",
            "objectives": ["进入森林", "探索区域", "返回报告"],
            "rewards": {"experience": 80, "gold": 30},
        }
        quest = await generator.generate_quest(
            region_id="region_core",
            chapter_id="chapter_01",
            quest_type="side",
            context={"theme": "探险", "difficulty": "normal"},
        )

        assert isinstance(quest, dict)
        assert "title" in quest

    @pytest.mark.asyncio
    async def test_generate_region(self, generator):
        """测试区域生成。"""
        generator.llm_adapter.mock_response = {
            "region_key": "region_forest",
            "name": "迷雾森林",
            "chapter_id": "chapter_01",
            "region_type": "core",
            "description": "一片神秘的森林，充满危险和机遇。古老的树木遮蔽了阳光，各种神秘的生物在此栖息。",
            "danger_level": "medium",
            "recommended_level": "1-10",
            "landmarks": [
                {
                    "landmark_key": "landmark_ruin",
                    "name": "失落遗迹",
                    "description": "埋藏在密林深处的古老石构建筑。",
                    "type": "ruin",
                    "significance": "蕴含上古文明的线索。",
                }
            ],
        }
        region = await generator.generate_region(
            chapter_id="chapter_01",
        )

        assert isinstance(region, dict)
        assert "name" in region
        assert "danger_level" in region
        assert "landmarks" in region

    @pytest.mark.asyncio
    async def test_generate_region_with_context(self, generator):
        """测试带上下文的区域生成。"""
        generator.llm_adapter.mock_response = {
            "region_key": "region_dark_forest",
            "name": "幽暗森林",
            "chapter_id": "chapter_01",
            "region_type": "expansion",
            "description": "一片幽暗的森林，阳光难以穿透茂密的树冠。",
            "danger_level": "high",
            "recommended_level": "5-15",
            "landmarks": [
                {
                    "landmark_key": "landmark_tree",
                    "name": "千年古树",
                    "description": "林中最为古老的树木，被视为神圣。",
                    "type": "natural",
                    "significance": "当地生物的庇护所。",
                }
            ],
        }
        region = await generator.generate_region(
            chapter_id="chapter_01",
            context={"theme": "森林", "difficulty": "normal"},
        )

        assert isinstance(region, dict)
        assert "name" in region

    @pytest.mark.asyncio
    async def test_generate_settlement(self, generator):
        """测试聚落生成。"""
        generator.llm_adapter.mock_response = {
            "settlement_key": "settlement_village_test",
            "name": "晨光村",
            "settlement_type": "village",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "faction_key": "faction_iron_guard",
            "description": "一座宁静的小村庄，以农业为主，村民们和睦相处，过着自给自足的生活。",
            "population": 200,
            "main_resources": ["谷物", "木材"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [
                {"location_key": "loc_center", "name": "广场", "description": "村庄中心广场"},
                {"location_key": "loc_inn", "name": "旅人旅馆", "description": "供旅行者休息的地方"},
            ],
            "key_npcs": ["npc_leader_01", "npc_trader_01"],
            "faction_influence": {"faction_iron_guard": "主导"},
            "relationships": {},
            "history": "晨光村建于数百年前，由一群逃难的农民建立。",
            "culture": "民风淳朴，重视传统和家庭。",
            "defenses": ["木墙", "守卫塔"],
            "services": ["旅馆", "商店", "铁匠"],
            "special_features": ["每周市集", "丰收节"],
            "location_x": 100,
            "location_y": 200,
        }
        settlement = await generator.generate_settlement(
            region_id="region_core",
            chapter_id="chapter_01",
            settlement_type="village",
        )

        assert isinstance(settlement, dict)
        assert "name" in settlement
        assert "settlement_type" in settlement
        assert "description" in settlement
        assert "population" in settlement

    @pytest.mark.asyncio
    async def test_generate_settlement_with_context(self, generator):
        """测试带上下文的聚落生成。"""
        generator.llm_adapter.mock_response = {
            "settlement_key": "settlement_town_test",
            "name": "铁砧镇",
            "settlement_type": "town",
            "region_key": "region_core",
            "chapter_id": "chapter_01",
            "faction_key": "faction_iron_guard",
            "description": "一座繁华的城镇，以锻造和贸易闻名。",
            "population": 800,
            "main_resources": ["矿石", "皮革"],
            "economy_type": "commerce",
            "status": "thriving",
            "notable_locations": [
                {"location_key": "loc_forge", "name": "铁砧工坊", "description": "著名的铁匠铺"},
            ],
            "key_npcs": ["npc_blacksmith_01"],
            "faction_influence": {"faction_iron_guard": "主导"},
            "relationships": {},
            "history": "铁砧镇因优质铁矿而发展起来。",
            "culture": "重视技艺和商业。",
            "defenses": ["石墙"],
            "services": ["铁匠", "商人", "银行"],
            "special_features": ["铁匠行会", "贸易市场"],
            "location_x": 150,
            "location_y": 250,
        }
        settlement = await generator.generate_settlement(
            region_id="region_core",
            chapter_id="chapter_01",
            settlement_type="town",
            context={"theme": "工业", "faction": "铁卫公会"},
        )

        assert isinstance(settlement, dict)
        assert "name" in settlement
        assert settlement["settlement_type"] == "town"


class TestPromptHardening:
    """WP1 提示词硬化（A3/A4/A5）落盘校验。

    验证 M4-模板文本细化.md 3.1/3.2/3.3/3.4 硬化文本已写入对应 live prompt 构造函数。
    真实 LLM 输出分布回归（A6）依赖运行时，不在本单测范围。
    """

    def test_item_prompt_contains_anchors(self, generator):
        """装备 prompt 应含 F2 数值锚定、F4 章节上限、F6 格式硬化。"""
        prompt = generator._build_item_prompt(
            region_id="region_core", chapter_id="chapter_03", item_type="weapon", context=None
        )
        assert "【数值锚定要求（F2）】" in prompt
        assert "weapon 的 attack 基值 = 6 + 4 × level_requirement" in prompt
        assert "稀有度系数：common=1.0" in prompt
        assert "【章节一致性约束（F4）】" in prompt
        assert "10 × N" in prompt
        assert "【输出格式要求（F6）】" in prompt
        assert "markdown 代码围栏" in prompt

    def test_monster_prompt_contains_anchors(self, generator):
        """怪物 prompt 应含 F3 数值锚定、F4 章节上限、F6 格式硬化。"""
        prompt = generator._build_monster_prompt(
            region_id="region_core", chapter_id="chapter_05", monster_type="dragon", context=None
        )
        assert "【数值锚定要求（F3）】" in prompt
        assert "hp 基值 = 40 + 26 × level" in prompt
        assert "类型系数：beast=1.0" in prompt
        assert "【章节一致性约束（F4）】" in prompt
        assert "输出格式要求（F6）" in prompt

    def test_boss_prompt_contains_anchors(self, generator):
        """Boss prompt 应显式引用 3.2 公式、含 F4 章节上限、F6 格式硬化。"""
        prompt = generator._build_boss_prompt(
            region_id="region_core", chapter_id="chapter_07", boss_rank="legendary", context=None
        )
        assert "Boss 数值锚定要求（F3 引用）" in prompt
        assert "hp ≥ 5 × 同等级普通怪物基值" in prompt
        assert "【章节一致性约束（F4）】" in prompt
        assert "输出格式要求（F6）" in prompt

    def test_region_prompt_contains_anchors(self, generator):
        """场景 prompt 应含 F4 章节上限（推荐等级带对齐）、F6 格式硬化。"""
        prompt = generator._build_region_prompt(chapter_id="chapter_04", context=None)
        assert "【章节一致性约束（F4）】" in prompt
        assert "recommended_level 必须与同章节怪物等级带" in prompt
        assert "输出格式要求（F6）" in prompt


class TestContentGenerationError:
    """内容生成错误测试。"""

    def test_error_creation(self):
        """测试错误创建。"""
        error = ContentGenerationError("Generation failed")
        assert str(error) == "Generation failed"

    def test_error_with_quality_score(self):
        """测试带质量分数的错误。"""
        error = ContentGenerationError("Quality too low", quality_score=0.5)
        assert error.quality_score == 0.5
