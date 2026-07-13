import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from system_designer_agent import SystemDesignerAgent
from designer_input_schemas import Task, TaskInput, RuleLibrary
from designer_output_schemas import DesignNote, DataStructure, ChangePlan, ArchitectureValidationReport
from designer_error_handler import (
    RequirementAmbiguityError,
    TechnicalFeasibilityError,
    ModuleConflictError,
    PerformanceRiskError,
    handle_requirement_ambiguity,
    handle_technical_feasibility,
    handle_module_conflict,
    handle_performance_risk,
)


@pytest.fixture
def sample_task_world():
    return Task(
        task_id="TASK-001",
        title="新增区域：迷雾森林",
        priority="P1",
        description="根据玩家投票结果，新增迷雾森林区域",
        requirements=["包含3个新NPC", "包含2个主线任务和3个支线任务", "支持探索和战斗玩法"],
        dependencies=[],
        assignee="world",
    )


@pytest.fixture
def sample_task_backend():
    return Task(
        task_id="TASK-002",
        title="新增任务系统接口",
        priority="P1",
        description="为任务系统新增创建和查询接口",
        requirements=["支持任务创建", "支持任务列表查询", "支持任务详情查询"],
        dependencies=["TASK-001"],
        assignee="backend",
    )


@pytest.fixture
def sample_rules():
    return RuleLibrary()


@pytest.fixture
def sample_task_input_world(sample_task_world, sample_rules):
    return TaskInput(task=sample_task_world, rules=sample_rules)


@pytest.fixture
def sample_task_input_backend(sample_task_backend, sample_rules):
    return TaskInput(task=sample_task_backend, rules=sample_rules)


def test_analyze_requirements(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.analyze_requirements(sample_task_input_world)

    assert isinstance(result, str)
    assert "任务分析：新增区域：迷雾森林" in result
    assert "优先级：P1" in result
    assert "包含3个新NPC" in result
    assert "负责代理：world" in result


def test_check_existing_system(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.check_existing_system(sample_task_input_world)

    assert isinstance(result, dict)
    assert "existing_modules" in result
    assert "world_rules" in result
    assert "constraints" in result
    assert "reusable_components" in result


def test_design_system_architecture_world(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.design_system_architecture(sample_task_input_world)

    assert isinstance(result, str)
    assert "系统架构设计：新增区域：迷雾森林" in result
    assert "world-service" in result
    assert "game/scenes/world" in result
    assert "数据流设计" in result


def test_design_system_architecture_backend(sample_task_input_backend):
    agent = SystemDesignerAgent()
    result = agent.design_system_architecture(sample_task_input_backend)

    assert isinstance(result, str)
    assert "vote-service" in result
    assert "content-service" in result


def test_define_data_structures_world(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.define_data_structures(sample_task_input_world)

    assert isinstance(result, list)
    assert len(result) > 0

    struct = result[0]
    assert isinstance(struct, DataStructure)
    assert struct.model_name == "Region"
    assert struct.table_name == "regions"
    assert len(struct.fields) > 0


def test_define_data_structures_backend(sample_task_input_backend):
    agent = SystemDesignerAgent()
    result = agent.define_data_structures(sample_task_input_backend)

    assert isinstance(result, list)
    assert len(result) > 0

    struct = result[0]
    assert isinstance(struct, DataStructure)
    assert struct.model_name == "QuestDefinition"
    assert struct.table_name == "quest_definitions"


def test_define_api_interfaces_world(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.define_api_interfaces(sample_task_input_world)

    assert isinstance(result, list)
    assert len(result) >= 2

    create_region = [i for i in result if i.method == "POST"]
    assert len(create_region) == 1
    assert create_region[0].endpoint == "/api/v1/world/regions"
    assert create_region[0].scope == "world:write"


def test_define_api_interfaces_backend(sample_task_input_backend):
    agent = SystemDesignerAgent()
    result = agent.define_api_interfaces(sample_task_input_backend)

    assert isinstance(result, list)
    assert len(result) >= 1

    create_quest = [i for i in result if i.method == "POST"]
    assert len(create_quest) == 1
    assert create_quest[0].endpoint == "/api/v1/ops/quests"
    assert create_quest[0].scope == "quests:write"


def test_generate_change_plan_world(sample_task_input_world):
    agent = SystemDesignerAgent()
    agent.analyze_requirements(sample_task_input_world)
    result = agent.generate_change_plan(sample_task_input_world)

    assert isinstance(result, ChangePlan)
    assert result.design_id.startswith("DESIGN-")
    assert len(result.modules) >= 2

    world_module = [m for m in result.modules if m.name == "world-service"]
    assert len(world_module) == 1
    assert len(world_module[0].changes) >= 3


def test_generate_change_plan_backend(sample_task_input_backend):
    agent = SystemDesignerAgent()
    agent.analyze_requirements(sample_task_input_backend)
    result = agent.generate_change_plan(sample_task_input_backend)

    assert isinstance(result, ChangePlan)
    assert result.design_id.startswith("DESIGN-")


def test_validate_architecture_with_requirements(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.validate_architecture(sample_task_input_world)

    assert isinstance(result, ArchitectureValidationReport)
    assert len(result.results) >= 4
    assert all(r.passed for r in result.results)
    assert result.overall_status == "approved"
    assert result.risk_score == 0.0


def test_validate_architecture_empty_requirements():
    task = Task(
        task_id="TASK-EMPTY",
        title="空需求任务",
        priority="P2",
        description="没有需求的任务",
        requirements=[],
        dependencies=[],
        assignee="world",
    )
    task_input = TaskInput(task=task, rules=RuleLibrary())

    agent = SystemDesignerAgent()
    result = agent.validate_architecture(task_input)

    assert isinstance(result, ArchitectureValidationReport)
    assert not all(r.passed for r in result.results)
    assert result.overall_status == "needs_revision"
    assert result.risk_score > 0


def test_deliver_design_document(sample_task_input_world):
    agent = SystemDesignerAgent()
    agent.analyze_requirements(sample_task_input_world)
    agent.design_system_architecture(sample_task_input_world)
    agent.define_data_structures(sample_task_input_world)
    agent.define_api_interfaces(sample_task_input_world)
    agent.generate_change_plan(sample_task_input_world)
    agent.validate_architecture(sample_task_input_world)

    result = agent.deliver_design_document(sample_task_input_world)

    assert isinstance(result, DesignNote)
    assert result.metadata.design_id.startswith("DESIGN-")
    assert result.metadata.task_id == "TASK-001"
    assert result.metadata.title == "新增区域：迷雾森林"
    assert len(result.data_structures) > 0
    assert len(result.interfaces) > 0


def test_execute_design_flow(sample_task_input_world):
    agent = SystemDesignerAgent()
    result = agent.execute_design_flow(sample_task_input_world)

    assert isinstance(result, DesignNote)
    assert result.metadata.status == "draft"
    assert result.validation_report is not None
    assert result.change_plan is not None


def test_error_handler_requirement_ambiguity():
    error = handle_requirement_ambiguity("测试任务", ["缺少描述", "缺少优先级"])

    assert isinstance(error, RequirementAmbiguityError)
    assert error.error_type == "requirement_ambiguity"
    assert len(error.missing_info) == 2


def test_error_handler_technical_feasibility():
    error = handle_technical_feasibility("测试任务", "技术栈不支持", ["方案A", "方案B"])

    assert isinstance(error, TechnicalFeasibilityError)
    assert error.error_type == "technical_feasibility"
    assert len(error.alternatives) == 2


def test_error_handler_module_conflict():
    error = handle_module_conflict("测试任务", ["moduleA", "moduleB"])

    assert isinstance(error, ModuleConflictError)
    assert error.error_type == "module_conflict"
    assert len(error.conflicting_modules) == 2


def test_error_handler_performance_risk():
    error = handle_performance_risk("测试任务", "high", ["添加缓存", "异步处理"])

    assert isinstance(error, PerformanceRiskError)
    assert error.error_type == "performance_risk"
    assert error.risk_level == "high"
    assert len(error.recommendations) == 2
