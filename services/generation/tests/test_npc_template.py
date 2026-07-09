"""NPC 模板管理测试。"""


from app.core.template_manager import TemplateManager


class TestNPCTemplateManager:
    def test_list_jinja_templates_npc(self):
        manager = TemplateManager()
        templates = manager.list_jinja_templates("npc")

        assert isinstance(templates, list)
        assert "npc/npc_base.jinja2" in templates
        assert "npc/npc_blacksmith.jinja2" in templates
        assert "npc/npc_merchant.jinja2" in templates
        assert "npc/npc_guard.jinja2" in templates
        assert "npc/npc_healer.jinja2" in templates
        assert "npc/npc_quest_giver.jinja2" in templates

    def test_get_npc_template_by_role(self):
        manager = TemplateManager()

        assert manager.get_npc_template_by_role("blacksmith") == "npc/npc_blacksmith.jinja2"
        assert manager.get_npc_template_by_role("merchant") == "npc/npc_merchant.jinja2"
        assert manager.get_npc_template_by_role("guard") == "npc/npc_guard.jinja2"
        assert manager.get_npc_template_by_role("healer") == "npc/npc_healer.jinja2"
        assert manager.get_npc_template_by_role("quest_giver") == "npc/npc_quest_giver.jinja2"
        assert manager.get_npc_template_by_role("unknown") == "npc/npc_base.jinja2"

    def test_render_jinja_template(self):
        manager = TemplateManager()
        template_name = "npc/npc_base.jinja2"

        rendered = manager.render_jinja_template(
            template_name,
            chapter_id="chapter_01",
            region_name="铁卫城周边",
            faction_name="铁卫联盟",
            world_rules="测试规则",
            npc_role="blacksmith",
            gender="male",
            race="human",
            faction_key="faction_ironward",
            region_key="region_core",
            location_x=100,
            location_y=200,
        )

        assert isinstance(rendered, str)
        assert "chapter_01" in rendered
        assert "铁卫城周边" in rendered
        assert "铁卫联盟" in rendered
        assert "blacksmith" in rendered
        assert "male" in rendered
        assert "human" in rendered