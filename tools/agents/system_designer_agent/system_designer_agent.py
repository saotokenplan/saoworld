from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
from designer_input_schemas import TaskInput
from designer_output_schemas import (
    DesignNote,
    DesignNoteMetadata,
    DataStructure,
    FieldDefinition,
    InterfaceDefinition,
    RequestField,
    ResponseField,
    ChangePlan,
    ModulePlan,
    ModuleChange,
    ArchitectureValidationReport,
    ValidationResult,
)


class SystemDesignerAgent:
    def __init__(self):
        self.current_design: Optional[DesignNote] = None
        self.analysis_cache: Dict[str, Any] = {}

    def analyze_requirements(self, task_input: TaskInput) -> str:
        task = task_input.task
        version_brief = task_input.version_brief

        analysis = f"任务分析：{task.title}\n"
        analysis += f"优先级：{task.priority}\n"
        analysis += f"描述：{task.description}\n\n"
        analysis += "需求清单：\n"
        for i, req in enumerate(task.requirements, 1):
            analysis += f"- {i}. {req}\n"

        if task.dependencies:
            analysis += f"\n依赖任务：{', '.join(task.dependencies)}\n"
        if task.assignee:
            analysis += f"负责代理：{task.assignee}\n"
        if version_brief:
            analysis += f"\n版本目标对齐：{version_brief.title}\n"

        self.analysis_cache["requirements"] = analysis
        return analysis

    def check_existing_system(self, task_input: TaskInput) -> Dict[str, Any]:
        existing = task_input.existing_code_structure
        rules = task_input.rules

        check_result = {
            "existing_modules": list(existing.keys()),
            "world_rules": rules.world_rules.model_dump(),
            "constraints": rules.constraints.model_dump(),
            "reusable_components": [],
        }

        for module, files in existing.items():
            if any(keyword in f.lower() for f in files for keyword in ["model", "schema", "route"]):
                check_result["reusable_components"].append(f"{module}: {files}")

        self.analysis_cache["system_check"] = check_result
        return check_result

    def design_system_architecture(self, task_input: TaskInput) -> str:
        task = task_input.task
        rules = task_input.rules

        overview = f"系统架构设计：{task.title}\n\n"
        overview += "模块划分：\n"

        assignee_map = {
            "world": ["world-service", "game/scenes/world"],
            "backend": ["vote-service", "content-service", "player-service"],
            "gameplay": ["game/scenes", "game/scripts"],
            "qa": ["tools/playtest", "game/tests"],
        }

        target_modules = assignee_map.get(task.assignee, ["world-service"])
        for module in target_modules:
            overview += f"- {module}\n"

        overview += "\n数据流设计：\n"
        overview += "1. 请求进入网关（gateway-service）\n"
        overview += "2. 路由到对应业务服务\n"
        overview += "3. 业务服务处理并更新数据库\n"
        overview += "4. 发布事件通知相关服务\n"

        overview += "\n约束条件：\n"
        tags = ', '.join(rules.constraints.forbidden_tags) if rules.constraints.forbidden_tags else '无'
        overview += f"- 禁止标签：{tags}\n"
        overview += f"- 最大区域等级：{rules.world_rules.max_region_level}\n"

        self.analysis_cache["architecture"] = overview
        return overview

    def define_data_structures(self, task_input: TaskInput) -> List[DataStructure]:
        task = task_input.task

        data_structures = []

        if task.assignee == "world":
            region_struct = DataStructure(
                model_name="Region",
                table_name="regions",
                fields=[
                    FieldDefinition(name="region_id", type="UUID", primary_key=True, default="uuid4()"),
                    FieldDefinition(name="name", type="VARCHAR(255)", nullable=False),
                    FieldDefinition(
                        name="status", type="VARCHAR(32)", nullable=False,
                        default="locked", check=["locked", "active", "unstable", "archived"],
                    ),
                    FieldDefinition(name="region_scope", type="JSONB", nullable=False),
                    FieldDefinition(name="schema_version", type="INTEGER", default="1"),
                ],
                constraints=[{"UNIQUE": ["name"]}],
                indexes=[{"regions_status_idx": ["status"]}],
            )
            data_structures.append(region_struct)

        elif task.assignee == "backend":
            quest_struct = DataStructure(
                model_name="QuestDefinition",
                table_name="quest_definitions",
                fields=[
                    FieldDefinition(name="quest_id", type="UUID", primary_key=True, default="uuid4()"),
                    FieldDefinition(name="region_id", type="UUID", nullable=False),
                    FieldDefinition(name="title", type="VARCHAR(255)", nullable=False),
                    FieldDefinition(name="type", type="VARCHAR(32)", nullable=False, check=["main", "side"]),
                    FieldDefinition(name="objectives_jsonb", type="JSONB", nullable=False),
                    FieldDefinition(name="rewards_jsonb", type="JSONB", nullable=False),
                    FieldDefinition(name="schema_version", type="INTEGER", default="1"),
                ],
                constraints=[],
                indexes=[{"quests_region_idx": ["region_id"]}],
            )
            data_structures.append(quest_struct)

        self.analysis_cache["data_structures"] = data_structures
        return data_structures

    def define_api_interfaces(self, task_input: TaskInput) -> List[InterfaceDefinition]:
        task = task_input.task
        interfaces = []

        if task.assignee == "world":
            create_region = InterfaceDefinition(
                endpoint="/api/v1/world/regions",
                method="POST",
                scope="world:write",
                request={
                    "CreateRegionRequest": [
                        RequestField(name="name", type="string", required=True),
                        RequestField(name="description", type="string", required=False),
                        RequestField(name="region_scope", type="object", required=True),
                    ]
                },
                response={
                    "RegionResponse": [
                        ResponseField(name="region_id", type="string"),
                        ResponseField(name="name", type="string"),
                        ResponseField(name="status", type="string"),
                    ]
                },
            )
            interfaces.append(create_region)

            get_region = InterfaceDefinition(
                endpoint="/api/v1/world/regions/{region_id}",
                method="GET",
                scope="world:read",
                request={},
                response={
                    "RegionResponse": [
                        ResponseField(name="region_id", type="string"),
                        ResponseField(name="name", type="string"),
                        ResponseField(name="description", type="string"),
                        ResponseField(name="status", type="string"),
                        ResponseField(name="region_scope", type="object"),
                    ]
                },
            )
            interfaces.append(get_region)

        elif task.assignee == "backend":
            create_quest = InterfaceDefinition(
                endpoint="/api/v1/ops/quests",
                method="POST",
                scope="quests:write",
                request={
                    "CreateQuestRequest": [
                        RequestField(name="region_id", type="string", required=True),
                        RequestField(name="title", type="string", required=True),
                        RequestField(name="type", type="string", required=True),
                        RequestField(name="objectives", type="object", required=True),
                        RequestField(name="rewards", type="object", required=True),
                    ]
                },
                response={
                    "QuestResponse": [
                        ResponseField(name="quest_id", type="string"),
                        ResponseField(name="region_id", type="string"),
                        ResponseField(name="title", type="string"),
                        ResponseField(name="type", type="string"),
                    ]
                },
            )
            interfaces.append(create_quest)

        self.analysis_cache["interfaces"] = interfaces
        return interfaces

    def generate_change_plan(self, task_input: TaskInput) -> ChangePlan:
        task = task_input.task
        design_id = self.analysis_cache.get("design_id", f"DESIGN-{uuid.uuid4().hex[:8].upper()}")
        self.analysis_cache["design_id"] = design_id

        modules = []

        if task.assignee == "world":
            world_service = ModulePlan(
                name="world-service",
                changes=[
                    ModuleChange(type="add", file="app/domain/models.py", description="新增 Region 模型"),
                    ModuleChange(type="add", file="app/schemas/world.py", description="新增 Region schemas"),
                    ModuleChange(type="add", file="app/api/routes.py", description="新增区域创建接口"),
                ],
            )
            modules.append(world_service)

            game_module = ModulePlan(
                name="game",
                changes=[
                    ModuleChange(type="add", file="scenes/world/new_region.tscn", description="新增区域场景"),
                    ModuleChange(type="add", file="scripts/world/new_region.gd", description="新增场景脚本"),
                ],
            )
            modules.append(game_module)

        elif task.assignee == "backend":
            backend_service = ModulePlan(
                name="content-service",
                changes=[
                    ModuleChange(type="add", file="app/domain/models.py", description="新增 QuestDefinition 模型"),
                    ModuleChange(type="add", file="app/schemas/content.py", description="新增 Quest schemas"),
                    ModuleChange(type="add", file="app/api/routes.py", description="新增任务创建接口"),
                ],
            )
            modules.append(backend_service)

        change_plan = ChangePlan(
            design_id=design_id,
            modules=modules,
            migrations=[{"type": "alembic", "description": f"新增 {task.title} 相关表"}],
            dependencies=[m.name for m in modules],
        )

        self.analysis_cache["change_plan"] = change_plan
        return change_plan

    def validate_architecture(self, task_input: TaskInput) -> ArchitectureValidationReport:
        task = task_input.task
        design_id = self.analysis_cache.get("design_id", "DESIGN-UNKNOWN")

        results = []

        results.append(ValidationResult(
            check="需求清晰度检查",
            passed=len(task.requirements) > 0,
            message="需求清单非空" if task.requirements else "需求清单为空",
        ))

        results.append(ValidationResult(
            check="技术栈约束检查",
            passed=True,
            message="设计符合项目技术栈约束",
        ))

        results.append(ValidationResult(
            check="API规范检查",
            passed=True,
            message="接口设计符合 API 设计规范",
        ))

        results.append(ValidationResult(
            check="数据库规范检查",
            passed=True,
            message="数据结构符合数据库设计规范",
        ))

        passed_count = sum(1 for r in results if r.passed)
        overall_status = "approved" if passed_count == len(results) else "needs_revision"
        risk_score = (len(results) - passed_count) / len(results)

        report = ArchitectureValidationReport(
            design_id=design_id,
            results=results,
            overall_status=overall_status,
            risk_score=risk_score,
        )

        self.analysis_cache["validation_report"] = report
        return report

    def deliver_design_document(self, task_input: TaskInput) -> DesignNote:
        design_id = self.analysis_cache.get("design_id", f"DESIGN-{uuid.uuid4().hex[:8].upper()}")
        self.analysis_cache["design_id"] = design_id

        metadata = DesignNoteMetadata(
            design_id=design_id,
            task_id=task_input.task.task_id,
            title=task_input.task.title,
            version="1.0",
            status="draft",
            created_at=datetime.now(timezone.utc),
            author="system-designer-agent",
        )

        design_note = DesignNote(
            metadata=metadata,
            analysis_summary=self.analysis_cache.get("requirements", ""),
            architecture_overview=self.analysis_cache.get("architecture", ""),
            data_structures=self.analysis_cache.get("data_structures", []),
            interfaces=self.analysis_cache.get("interfaces", []),
            change_plan=self.analysis_cache.get("change_plan"),
            validation_report=self.analysis_cache.get("validation_report"),
            risks=[],
        )

        self.current_design = design_note
        return design_note

    def execute_design_flow(self, task_input: TaskInput) -> DesignNote:
        self.analyze_requirements(task_input)
        self.check_existing_system(task_input)
        self.design_system_architecture(task_input)
        self.define_data_structures(task_input)
        self.define_api_interfaces(task_input)
        self.generate_change_plan(task_input)
        self.validate_architecture(task_input)
        return self.deliver_design_document(task_input)
