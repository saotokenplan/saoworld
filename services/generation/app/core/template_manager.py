import json
import os
from typing import Any, TypedDict

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


template_manager = TemplateManager()
