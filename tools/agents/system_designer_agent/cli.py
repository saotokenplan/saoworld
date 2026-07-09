import click
import json
from .system_designer_agent import SystemDesignerAgent
from .designer_input_schemas import Task, TaskInput, RuleLibrary


@click.group()
def cli():
    pass


@cli.command("design-system")
@click.option("--task-id", required=True, help="任务ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--priority", default="P1", help="优先级：P0/P1/P2/P3")
@click.option("--description", required=True, help="任务描述")
@click.option("--requirement", multiple=True, help="需求项（可多次指定）")
@click.option("--assignee", required=True, help="负责代理：world/backend/gameplay/qa")
@click.option("--output", default="design-note.json", help="输出文件路径")
def design_system(task_id: str, title: str, priority: str, description: str, requirement: tuple, assignee: str, output: str):
    agent = SystemDesignerAgent()

    task = Task(
        task_id=task_id,
        title=title,
        priority=priority,
        description=description,
        requirements=list(requirement),
        dependencies=[],
        assignee=assignee,
    )

    rules = RuleLibrary()
    task_input = TaskInput(task=task, rules=rules)

    design_note = agent.execute_design_flow(task_input)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(design_note.dict(), f, indent=2, default=str)

    click.echo(f"设计文档已生成：{output}")
    click.echo(f"设计ID：{design_note.metadata.design_id}")
    click.echo(f"状态：{design_note.metadata.status}")


@cli.command("define-data-structure")
@click.option("--model-name", required=True, help="模型名称")
@click.option("--table-name", required=True, help="表名称")
@click.option("--field", multiple=True, help="字段定义：name:type[:primary_key][:nullable]")
@click.option("--output", default="data-structure.json", help="输出文件路径")
def define_data_structure(model_name: str, table_name: str, field: tuple, output: str):
    agent = SystemDesignerAgent()

    task = Task(
        task_id="CLI-001",
        title=f"定义数据结构：{model_name}",
        priority="P1",
        description=f"为 {model_name} 定义数据结构",
        requirements=[],
        dependencies=[],
        assignee="backend",
    )

    rules = RuleLibrary()
    task_input = TaskInput(task=task, rules=rules)

    agent.analyze_requirements(task_input)
    data_structures = agent.define_data_structures(task_input)

    result = {"model_name": model_name, "table_name": table_name, "structures": [ds.dict() for ds in data_structures]}

    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    click.echo(f"数据结构已生成：{output}")


@cli.command("generate-change-plan")
@click.option("--task-id", required=True, help="任务ID")
@click.option("--title", required=True, help="任务标题")
@click.option("--assignee", required=True, help="负责代理")
@click.option("--output", default="change-plan.json", help="输出文件路径")
def generate_change_plan(task_id: str, title: str, assignee: str, output: str):
    agent = SystemDesignerAgent()

    task = Task(
        task_id=task_id,
        title=title,
        priority="P1",
        description=f"生成改动计划：{title}",
        requirements=[],
        dependencies=[],
        assignee=assignee,
    )

    rules = RuleLibrary()
    task_input = TaskInput(task=task, rules=rules)

    agent.analyze_requirements(task_input)
    change_plan = agent.generate_change_plan(task_input)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(change_plan.dict(), f, indent=2, default=str)

    click.echo(f"改动计划已生成：{output}")
    click.echo(f"设计ID：{change_plan.design_id}")
    click.echo(f"涉及模块：{', '.join(m.name for m in change_plan.modules)}")


if __name__ == "__main__":
    cli()