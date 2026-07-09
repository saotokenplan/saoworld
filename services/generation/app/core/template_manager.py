import json
import os
from typing import Any, TypedDict

from jinja2 import Environment, FileSystemLoader

from app.core.config import settings


class GenerationTemplate(TypedDict):
    template_id: str
    template_type: str
    version: str
    name: str
    description: str
    region_ids: list[str] | None
    chapter_ids: list[str] | None
    schema_version: int
    prompt_template: str
    required_fields: list[str]
    optional_fields: list[str]


class TemplateManager:
    def __init__(self, template_dir: str | None = None):
        self.template_dir = template_dir or settings.template_dir
        self._templates: dict[str, GenerationTemplate] = {}
        self._templates_by_type: dict[str, list[GenerationTemplate]] = {}
        self._jinja_env: Environment | None = None

    def _init_jinja(self) -> Environment:
        if self._jinja_env is None:
            template_paths = [self.template_dir]
            npc_dir = os.path.join(self.template_dir, "npc")
            if os.path.exists(npc_dir):
                template_paths.append(npc_dir)
            quest_dir = os.path.join(self.template_dir, "quest")
            if os.path.exists(quest_dir):
                template_paths.append(quest_dir)
            region_dir = os.path.join(self.template_dir, "region")
            if os.path.exists(region_dir):
                template_paths.append(region_dir)
            self._jinja_env = Environment(
                loader=FileSystemLoader(template_paths),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return self._jinja_env

    def load_templates(self) -> None:
        if not os.path.exists(self.template_dir):
            return

        for filename in os.listdir(self.template_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.template_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                        template = GenerationTemplate(
                            template_id=template_data["template_id"],
                            template_type=template_data["template_type"],
                            version=template_data["version"],
                            name=template_data["name"],
                            description=template_data["description"],
                            region_ids=template_data.get("region_ids"),
                            chapter_ids=template_data.get("chapter_ids"),
                            schema_version=template_data.get("schema_version", 1),
                            prompt_template=template_data["prompt_template"],
                            required_fields=template_data.get("required_fields", []),
                            optional_fields=template_data.get("optional_fields", []),
                        )
                        self._templates[template["template_id"]] = template
                        if template["template_type"] not in self._templates_by_type:
                            self._templates_by_type[template["template_type"]] = []
                        self._templates_by_type[template["template_type"]].append(template)
                except Exception:
                    continue

    def get_template(self, template_id: str) -> GenerationTemplate | None:
        return self._templates.get(template_id)

    def list_templates(self) -> list[GenerationTemplate]:
        return list(self._templates.values())

    def list_templates_by_type(self, template_type: str) -> list[GenerationTemplate]:
        return self._templates_by_type.get(template_type, [])

    def match_template(
        self,
        target_type: str,
        region_id: str | None = None,
        chapter_id: str | None = None,
        npc_role: str | None = None,
    ) -> GenerationTemplate | None:
        candidates = self.list_templates_by_type(target_type)
        if not candidates:
            return None

        for candidate in candidates:
            if candidate["region_ids"] and region_id and region_id not in candidate["region_ids"]:
                continue
            if candidate["chapter_ids"] and chapter_id and chapter_id not in candidate["chapter_ids"]:
                continue
            return candidate

        return candidates[0]

    def render_prompt(self, template: GenerationTemplate, **kwargs: Any) -> str:
        prompt = template["prompt_template"]
        return prompt.format(**kwargs)

    def render_jinja_template(self, template_name: str, **kwargs: Any) -> str:
        jinja_env = self._init_jinja()
        template = jinja_env.get_template(template_name)
        return template.render(**kwargs)

    def list_jinja_templates(self, template_type: str) -> list[str]:
        type_dir = os.path.join(self.template_dir, template_type)
        if not os.path.exists(type_dir):
            return []
        templates = []
        for filename in os.listdir(type_dir):
            if filename.endswith(".jinja2"):
                templates.append(os.path.join(template_type, filename))
        return templates

    def get_npc_template_by_role(self, role: str) -> str | None:
        role_map = {
            "blacksmith": "npc/npc_blacksmith.jinja2",
            "merchant": "npc/npc_merchant.jinja2",
            "guard": "npc/npc_guard.jinja2",
            "healer": "npc/npc_healer.jinja2",
            "quest_giver": "npc/npc_quest_giver.jinja2",
        }
        return role_map.get(role) or "npc/npc_base.jinja2"


template_manager = TemplateManager()