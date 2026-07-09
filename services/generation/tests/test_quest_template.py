"""任务模板管理测试。"""

from app.core.template_manager import TemplateManager


class TestQuestTemplateManager:
    def test_list_jinja_templates_quest(self):
        manager = TemplateManager()
        templates = manager.list_jinja_templates("quest")

        assert isinstance(templates, list)
        assert "quest/quest_base.jinja2" in templates
        assert "quest/quest_main.jinja2" in templates
        assert "quest/quest_side.jinja2" in templates
        assert "quest/quest_event.jinja2" in templates
        assert "quest/quest_daily.jinja2" in templates

    def test_get_quest_template_by_type(self):
        manager = TemplateManager()

        assert manager.get_quest_template_by_type("main") == "quest/quest_main.jinja2"
        assert manager.get_quest_template_by_type("side") == "quest/quest_side.jinja2"
        assert manager.get_quest_template_by_type("event") == "quest/quest_event.jinja2"
        assert manager.get_quest_template_by_type("daily") == "quest/quest_daily.jinja2"
        assert manager.get_quest_template_by_type("unknown") == "quest/quest_base.jinja2"

    def test_render_jinja_template_quest_main(self):
        manager = TemplateManager()
        template_name = "quest/quest_main.jinja2"

        rendered = manager.render_jinja_template(
            template_name,
            chapter_id="chapter_01",
            region_name="铁卫城周边",
            faction_name="铁卫联盟",
            world_rules="测试规则",
            quest_type="main",
            region_key="region_core",
            faction_key="faction_ironward",
            start_npc_key="npc_ironward_leader",
            end_npc_key="npc_ironward_leader",
        )

        assert isinstance(rendered, str)
        assert "chapter_01" in rendered
        assert "铁卫城周边" in rendered
        assert "铁卫联盟" in rendered
        assert "main" in rendered
        assert "npc_ironward_leader" in rendered

    def test_render_jinja_template_quest_side(self):
        manager = TemplateManager()
        template_name = "quest/quest_side.jinja2"

        rendered = manager.render_jinja_template(
            template_name,
            chapter_id="chapter_02",
            region_name="灰谷废墟",
            faction_name="暗影面纱",
            world_rules="测试规则",
            quest_type="side",
            region_key="region_expansion",
            faction_key="faction_shadowveil",
            start_npc_key="npc_shadowveil_researcher",
            end_npc_key="npc_shadowveil_researcher",
        )

        assert isinstance(rendered, str)
        assert "chapter_02" in rendered
        assert "灰谷废墟" in rendered
        assert "暗影面纱" in rendered
        assert "side" in rendered

    def test_render_jinja_template_quest_event(self):
        manager = TemplateManager()
        template_name = "quest/quest_event.jinja2"

        rendered = manager.render_jinja_template(
            template_name,
            chapter_id="chapter_02",
            region_name="灰谷废墟",
            faction_name="自由领地",
            world_rules="测试规则",
            quest_type="event",
            region_key="region_expansion",
            faction_key="faction_freedom",
            start_npc_key="npc_scavenger_leader",
            end_npc_key="npc_scavenger_leader",
        )

        assert isinstance(rendered, str)
        assert "event" in rendered

    def test_render_jinja_template_quest_daily(self):
        manager = TemplateManager()
        template_name = "quest/quest_daily.jinja2"

        rendered = manager.render_jinja_template(
            template_name,
            chapter_id="chapter_01",
            region_name="铁卫城周边",
            faction_name="铁卫联盟",
            world_rules="测试规则",
            quest_type="daily",
            region_key="region_core",
            faction_key="faction_ironward",
            start_npc_key="npc_guard",
            end_npc_key="npc_guard",
        )

        assert isinstance(rendered, str)
        assert "daily" in rendered