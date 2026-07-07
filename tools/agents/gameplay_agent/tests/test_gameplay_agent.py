import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from gameplay_agent import GameplayAgent
from input_schemas import (
    DesignTask, SceneConfig, ScriptInterface, DataConfig, GameplayTaskInput,
    SceneNode, ScriptProperty, ScriptMethod, SignalDefinition,
)
from error_handler import (
    IncompleteDesignError, MissingDataConfigError,
)


def test_analyze_design_document():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景文件", "创建脚本文件", "包含区域渲染"],
        data_config="game/data/regions/fog_forest.json",
    )

    scene_config = SceneConfig(
        scene_name="fog_forest",
        nodes=[SceneNode(name="Background", type="Sprite2D")],
        signals=[SignalDefinition(name="region_selected", parameters=[{"name": "region_id", "type": "String"}])],
    )

    script_interface = ScriptInterface(
        script_name="fog_forest",
        extends="Node2D",
        properties=[ScriptProperty(name="region_id", type="String", default='"region_fog_forest"')],
        methods=[ScriptMethod(name="_ready", return_type="void", parameters=[])],
    )

    task_input = GameplayTaskInput(
        design_task=design_task,
        scene_config=scene_config,
        script_interface=script_interface,
    )

    agent = GameplayAgent()
    analysis = agent.analyze_design_document(task_input)

    assert analysis["design_id"] == "DESIGN-001"
    assert analysis["task_id"] == "TASK-001"
    assert analysis["title"] == "新增迷雾森林场景"
    assert analysis["requirements_count"] == 3
    assert analysis["has_data_config"] is True
    assert analysis["scene_config_present"] is True
    assert analysis["script_interface_present"] is True
    assert analysis["nodes_count"] == 1
    assert analysis["signals_count"] == 1
    assert analysis["properties_count"] == 1
    assert analysis["methods_count"] == 1


def test_analyze_design_document_missing_requirements():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增场景",
        type="scene",
        target_module="world",
        requirements=[],
    )

    task_input = GameplayTaskInput(design_task=design_task)
    agent = GameplayAgent()

    with pytest.raises(IncompleteDesignError):
        agent.analyze_design_document(task_input)


def test_check_existing_code():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
        data_config="game/data/regions/fog_forest.json",
    )

    scene_config = SceneConfig(scene_name="fog_forest", nodes=[], signals=[])
    script_interface = ScriptInterface(script_name="fog_forest", extends="Node2D")

    task_input = GameplayTaskInput(
        design_task=design_task,
        scene_config=scene_config,
        script_interface=script_interface,
    )

    agent = GameplayAgent()
    check_result = agent.check_existing_code(task_input)

    assert check_result["target_module"] == "world"
    assert len(check_result["existing_data"]) == 1
    assert len(check_result["existing_scenes"]) == 1
    assert len(check_result["existing_scripts"]) == 1
    assert "data_config" in check_result["reusable_components"]


def test_create_scene_file():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    scene_config = SceneConfig(
        scene_name="fog_forest",
        nodes=[SceneNode(name="Background", type="Sprite2D", properties={"texture": '"res://assets/tiles/fog_forest.png"'})],
        signals=[SignalDefinition(name="region_selected", parameters=[{"name": "region_id", "type": "String"}])],
    )

    task_input = GameplayTaskInput(design_task=design_task, scene_config=scene_config)

    agent = GameplayAgent()
    scene_output = agent.create_scene_file(task_input)

    assert scene_output.scene_id.startswith("SCENE-")
    assert scene_output.design_id == "DESIGN-001"
    assert scene_output.file_path == "scenes/world/fog_forest.tscn"
    assert scene_output.script_path == "scripts/world/fog_forest.gd"


def test_create_scene_file_missing_config():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    task_input = GameplayTaskInput(design_task=design_task)
    agent = GameplayAgent()

    with pytest.raises(IncompleteDesignError):
        agent.create_scene_file(task_input)


def test_write_script_logic():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林脚本",
        type="script",
        target_module="world",
        requirements=["编写脚本"],
    )

    script_interface = ScriptInterface(
        script_name="fog_forest",
        extends="Node2D",
        properties=[
            ScriptProperty(name="region_id", type="String", default='"region_fog_forest"'),
            ScriptProperty(name="is_unlocked", type="bool", default="false"),
        ],
        methods=[
            ScriptMethod(name="_ready", return_type="void", parameters=[]),
            ScriptMethod(name="on_region_click", return_type="void", parameters=[{"name": "event", "type": "InputEventMouseButton"}]),
        ],
    )

    task_input = GameplayTaskInput(design_task=design_task, script_interface=script_interface)

    agent = GameplayAgent()
    script_output = agent.write_script_logic(task_input)

    assert script_output.script_id.startswith("SCRIPT-")
    assert script_output.file_path == "scripts/world/fog_forest.gd"
    assert script_output.extends == "Node2D"
    assert script_output.properties_count == 2
    assert script_output.methods_count == 2


def test_write_script_logic_missing_interface():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增脚本",
        type="script",
        target_module="world",
        requirements=["编写脚本"],
    )

    task_input = GameplayTaskInput(design_task=design_task)
    agent = GameplayAgent()

    with pytest.raises(IncompleteDesignError):
        agent.write_script_logic(task_input)


def test_integrate_data_config():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="集成区域数据",
        type="scene",
        target_module="world",
        requirements=["集成数据"],
        data_config="game/data/regions/fog_forest.json",
    )

    task_input = GameplayTaskInput(design_task=design_task)

    agent = GameplayAgent()
    integration_result = agent.integrate_data_config(task_input)

    assert integration_result["data_path"] == "game/data/regions/fog_forest.json"
    assert integration_result["schema_version"] == 1
    assert len(integration_result["integration_points"]) == 3


def test_integrate_data_config_with_data_config():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="集成区域数据",
        type="scene",
        target_module="world",
        requirements=["集成数据"],
    )

    data_config = DataConfig(
        data_path="game/data/regions/fog_forest.json",
        schema_version=2,
        data_type="region",
    )

    task_input = GameplayTaskInput(design_task=design_task, data_config=data_config)

    agent = GameplayAgent()
    integration_result = agent.integrate_data_config(task_input)

    assert integration_result["data_path"] == "game/data/regions/fog_forest.json"
    assert integration_result["schema_version"] == 2
    assert integration_result["data_type"] == "region"


def test_integrate_data_config_missing():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="集成数据",
        type="scene",
        target_module="world",
        requirements=["集成数据"],
    )

    task_input = GameplayTaskInput(design_task=design_task)
    agent = GameplayAgent()

    with pytest.raises(MissingDataConfigError):
        agent.integrate_data_config(task_input)


def test_write_test_cases():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    task_input = GameplayTaskInput(design_task=design_task)

    agent = GameplayAgent()
    test_output = agent.write_test_cases(task_input)

    assert test_output.test_file == "tests/test_新增迷雾森林场景.gd"
    assert test_output.total_tests == 4
    assert len(test_output.tests) == 4
    assert test_output.tests[0].name == "test_scene_loading"


def test_run_tests_and_verify():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    task_input = GameplayTaskInput(design_task=design_task)

    agent = GameplayAgent()
    test_result = agent.run_tests_and_verify(task_input)

    assert test_result["status"] == "success"
    assert test_result["passed"] == 4
    assert test_result["failed"] == 0


def test_deliver_output():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    scene_config = SceneConfig(scene_name="fog_forest", nodes=[], signals=[])
    script_interface = ScriptInterface(script_name="fog_forest", extends="Node2D")

    task_input = GameplayTaskInput(design_task=design_task, scene_config=scene_config, script_interface=script_interface)

    agent = GameplayAgent()
    agent.analyze_design_document(task_input)
    agent.check_existing_code(task_input)
    agent.create_scene_file(task_input)
    agent.write_script_logic(task_input)
    agent.write_test_cases(task_input)

    result = agent.deliver_output(task_input)

    assert result.result_id.startswith("RESULT-")
    assert result.task_id == "TASK-001"
    assert result.design_id == "DESIGN-001"
    assert result.status == "completed"
    assert result.scene_output is not None
    assert result.script_output is not None
    assert result.test_output is not None


def test_execute_gameplay_flow():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="新增迷雾森林场景",
        type="scene",
        target_module="world",
        requirements=["创建场景文件", "创建脚本文件", "包含区域渲染"],
        data_config="game/data/regions/fog_forest.json",
    )

    scene_config = SceneConfig(
        scene_name="fog_forest",
        nodes=[SceneNode(name="Background", type="Sprite2D")],
        signals=[SignalDefinition(name="region_selected", parameters=[{"name": "region_id", "type": "String"}])],
    )

    script_interface = ScriptInterface(
        script_name="fog_forest",
        extends="Node2D",
        properties=[ScriptProperty(name="region_id", type="String")],
        methods=[ScriptMethod(name="_ready", return_type="void", parameters=[])],
    )

    data_config = DataConfig(
        data_path="game/data/regions/fog_forest.json",
        schema_version=1,
        data_type="region",
    )

    task_input = GameplayTaskInput(
        design_task=design_task,
        scene_config=scene_config,
        script_interface=script_interface,
        data_config=data_config,
    )

    agent = GameplayAgent()
    result = agent.execute_gameplay_flow(task_input)

    assert result.status == "completed"
    assert result.scene_output is not None
    assert result.script_output is not None
    assert result.test_output is not None


def test_execute_gameplay_flow_failure():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="失败场景",
        type="scene",
        target_module="world",
        requirements=[],
    )

    task_input = GameplayTaskInput(design_task=design_task)

    agent = GameplayAgent()
    result = agent.execute_gameplay_flow(task_input)

    assert result.status == "failed"
    assert "设计文档缺少关键需求信息" in result.error_message


def test_execute_gameplay_flow_without_data_config():
    design_task = DesignTask(
        design_id="DESIGN-001",
        task_id="TASK-001",
        title="无数据配置场景",
        type="scene",
        target_module="world",
        requirements=["创建场景"],
    )

    scene_config = SceneConfig(scene_name="test_scene", nodes=[], signals=[])

    task_input = GameplayTaskInput(design_task=design_task, scene_config=scene_config)

    agent = GameplayAgent()
    result = agent.execute_gameplay_flow(task_input)

    assert result.status == "completed"
    assert result.scene_output is not None
    assert result.test_output is not None