import os
import tempfile
import json

from app.core.template_manager import TemplateManager, GenerationTemplate


class TestTemplateManager:
    def test_load_templates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            template_data = {
                "template_id": "tpl_test_v1",
                "template_type": "npc",
                "version": "1.0",
                "name": "Test Template",
                "description": "Test description",
                "region_ids": ["region_test"],
                "chapter_ids": ["chapter_01"],
                "schema_version": 1,
                "prompt_template": "Test prompt {name}",
                "required_fields": ["name"],
                "optional_fields": ["description"],
            }
            template_path = os.path.join(tmpdir, "test_template.json")
            with open(template_path, "w") as f:
                json.dump(template_data, f)

            manager = TemplateManager(tmpdir)
            manager.load_templates()

            templates = manager.list_templates()
            assert len(templates) == 1
            assert templates[0]["template_id"] == "tpl_test_v1"

    def test_get_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            template_data = {
                "template_id": "tpl_get_v1",
                "template_type": "npc",
                "version": "1.0",
                "name": "Get Template",
                "description": "Test",
                "region_ids": None,
                "chapter_ids": None,
                "schema_version": 1,
                "prompt_template": "Test",
                "required_fields": [],
                "optional_fields": [],
            }
            template_path = os.path.join(tmpdir, "tpl_get_v1.json")
            with open(template_path, "w") as f:
                json.dump(template_data, f)

            manager = TemplateManager(tmpdir)
            manager.load_templates()

            template = manager.get_template("tpl_get_v1")
            assert template is not None
            assert template["name"] == "Get Template"

            not_found = manager.get_template("nonexistent")
            assert not_found is None

    def test_list_templates_by_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            npc_template = {
                "template_id": "tpl_npc_v1",
                "template_type": "npc",
                "version": "1.0",
                "name": "NPC Template",
                "description": "Test",
                "region_ids": None,
                "chapter_ids": None,
                "schema_version": 1,
                "prompt_template": "Test",
                "required_fields": [],
                "optional_fields": [],
            }
            quest_template = {
                "template_id": "tpl_quest_v1",
                "template_type": "quest",
                "version": "1.0",
                "name": "Quest Template",
                "description": "Test",
                "region_ids": None,
                "chapter_ids": None,
                "schema_version": 1,
                "prompt_template": "Test",
                "required_fields": [],
                "optional_fields": [],
            }

            with open(os.path.join(tmpdir, "npc.json"), "w") as f:
                json.dump(npc_template, f)
            with open(os.path.join(tmpdir, "quest.json"), "w") as f:
                json.dump(quest_template, f)

            manager = TemplateManager(tmpdir)
            manager.load_templates()

            npc_templates = manager.list_templates_by_type("npc")
            assert len(npc_templates) == 1
            assert npc_templates[0]["template_type"] == "npc"

            quest_templates = manager.list_templates_by_type("quest")
            assert len(quest_templates) == 1
            assert quest_templates[0]["template_type"] == "quest"

            empty = manager.list_templates_by_type("nonexistent")
            assert len(empty) == 0

    def test_match_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            npc_template = {
                "template_id": "tpl_npc_v1",
                "template_type": "npc",
                "version": "1.0",
                "name": "NPC Template",
                "description": "Test",
                "region_ids": ["region_core", "region_expansion"],
                "chapter_ids": ["chapter_01", "chapter_02"],
                "schema_version": 1,
                "prompt_template": "Test",
                "required_fields": [],
                "optional_fields": [],
            }

            with open(os.path.join(tmpdir, "npc.json"), "w") as f:
                json.dump(npc_template, f)

            manager = TemplateManager(tmpdir)
            manager.load_templates()

            matched = manager.match_template("npc", "region_core", "chapter_01")
            assert matched is not None
            assert matched["template_id"] == "tpl_npc_v1"

            matched_no_region = manager.match_template("npc", None, None)
            assert matched_no_region is not None

            unmatched = manager.match_template("nonexistent", "region_core", "chapter_01")
            assert unmatched is None

    def test_render_prompt(self):
        template = GenerationTemplate(
            template_id="tpl_test_v1",
            template_type="npc",
            version="1.0",
            name="Test Template",
            description="Test",
            region_ids=None,
            chapter_ids=None,
            schema_version=1,
            prompt_template="Hello {name}, you are in {region}",
            required_fields=["name"],
            optional_fields=["region"],
        )

        manager = TemplateManager()
        rendered = manager.render_prompt(template, name="Player", region="Iron Guard")
        assert rendered == "Hello Player, you are in Iron Guard"
