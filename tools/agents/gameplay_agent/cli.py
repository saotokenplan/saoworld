import click
import json
from .gameplay_agent import GameplayAgent
from .input_schemas import DesignTask, SceneConfig, ScriptInterface, DataConfig, GameplayTaskInput, SceneNode, ScriptProperty, ScriptMethod, SignalDefinition


@click.group()
def cli():
    pass


@cli.command()
@click.option("--design-id", required=True, help="设计文档ID")
@click.option("--task-id", required=True, help="任务ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--type", required=True, help="任务类型（scene/script/ui）")
@click.option("--target-module", required=True, help="目标模块（game/world/ui）")
@click.option("--requirement", multiple=True, help="需求项")
@click.option("--data-config", help="数据配置文件路径")
def create_scene(design_id, task_id, title, type, target_module, requirement, data_config):
    agent = GameplayAgent()

    design_task = DesignTask(
        design_id=design_id,
        task_id=task_id,
        title=title,
        type=type,
        target_module=target_module,
        requirements=list(requirement),
        data_config=data_config,
    )

    scene_config = SceneConfig(
        scene_name=title.lower().replace(" ", "_"),
        nodes=[
            SceneNode(name="Background", type="Sprite2D", properties={"texture": f'"res://assets/tiles/{title.lower().replace(" ", "_")}.png"'})
        ],
        signals=[
            SignalDefinition(name="region_selected", parameters=[{"name": "region_id", "type": "String"}])
        ],
    )

    task_input = GameplayTaskInput(design_task=design_task, scene_config=scene_config)

    result = agent.execute_gameplay_flow(task_input)
    click.echo(f"场景创建完成: {result.scene_output.file_path}")


@cli.command()
@click.option("--design-id", required=True, help="设计文档ID")
@click.option("--task-id", required=True, help="任务ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--type", required=True, help="任务类型（scene/script/ui）")
@click.option("--target-module", required=True, help="目标模块（game/world/ui）")
@click.option("--script-name", required=True, help="脚本名称")
@click.option("--extends", default="Node2D", help="继承类")
@click.option("--property", multiple=True, help="属性定义（name:type:default）")
@click.option("--method", multiple=True, help="方法定义（name:return_type:param1:type1）")
def write_script(design_id, task_id, title, type, target_module, script_name, extends, property, method):
    agent = GameplayAgent()

    design_task = DesignTask(
        design_id=design_id,
        task_id=task_id,
        title=title,
        type=type,
        target_module=target_module,
        requirements=["创建脚本"],
    )

    properties = []
    for p in property:
        parts = p.split(":")
        props = {"name": parts[0], "type": parts[1]}
        if len(parts) > 2:
            props["default"] = parts[2]
        properties.append(ScriptProperty(**props))

    methods = []
    for m in method:
        parts = m.split(":")
        method_params = []
        if len(parts) > 2:
            for i in range(2, len(parts), 2):
                if i + 1 < len(parts):
                    method_params.append({"name": parts[i], "type": parts[i + 1]})
        methods.append(ScriptMethod(name=parts[0], return_type=parts[1], parameters=method_params))

    script_interface = ScriptInterface(
        script_name=script_name,
        extends=extends,
        properties=properties,
        methods=methods,
    )

    task_input = GameplayTaskInput(design_task=design_task, script_interface=script_interface)

    result = agent.execute_gameplay_flow(task_input)
    click.echo(f"脚本编写完成: {result.script_output.file_path}")


@cli.command()
@click.option("--design-id", required=True, help="设计文档ID")
@click.option("--task-id", required=True, help="任务ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--type", required=True, help="任务类型")
@click.option("--target-module", required=True, help="目标模块")
def generate_test(design_id, task_id, title, type, target_module):
    agent = GameplayAgent()

    design_task = DesignTask(
        design_id=design_id,
        task_id=task_id,
        title=title,
        type=type,
        target_module=target_module,
        requirements=["生成测试用例"],
    )

    task_input = GameplayTaskInput(design_task=design_task)

    result = agent.execute_gameplay_flow(task_input)
    click.echo(f"测试用例生成完成: {result.test_output.test_file}")
    click.echo(f"测试用例数量: {result.test_output.total_tests}")


@cli.command()
@click.option("--input-file", required=True, help="输入配置文件路径")
def run_workflow(input_file):
    agent = GameplayAgent()

    with open(input_file, "r") as f:
        input_data = json.load(f)

    design_task = DesignTask(**input_data["design_task"])
    scene_config = SceneConfig(**input_data["scene_config"]) if "scene_config" in input_data else None
    script_interface = ScriptInterface(**input_data["script_interface"]) if "script_interface" in input_data else None
    data_config = DataConfig(**input_data["data_config"]) if "data_config" in input_data else None

    task_input = GameplayTaskInput(
        design_task=design_task,
        scene_config=scene_config,
        script_interface=script_interface,
        data_config=data_config,
    )

    result = agent.execute_gameplay_flow(task_input)

    output = {
        "result_id": result.result_id,
        "task_id": result.task_id,
        "design_id": result.design_id,
        "status": result.status,
    }

    if result.scene_output:
        output["scene_output"] = result.scene_output.model_dump()
    if result.script_output:
        output["script_output"] = result.script_output.model_dump()
    if result.test_output:
        output["test_output"] = result.test_output.model_dump()

    click.echo(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli()
