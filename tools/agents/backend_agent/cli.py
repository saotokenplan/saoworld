"""
Backend Agent CLI 命令行工具

提供 implement-model、implement-route、generate-test、run-workflow 四个命令。
"""

import json
import sys
from pathlib import Path

import click

from .backend_agent import BackendAgent
from .input_schemas import BackendAgentInput, DataStructure, DesignTask, ExistingCode


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """Backend Agent 命令行工具"""
    pass


@cli.command()
@click.option("--service", required=True, help="目标服务名称")
@click.option("--model-name", required=True, help="模型名称")
@click.option("--table-name", required=True, help="表名")
@click.option("--fields-file", required=True, help="字段定义 JSON 文件路径")
@click.option("--output-dir", default=".", help="输出目录")
def implement_model(
    service: str, model_name: str, table_name: str, fields_file: str, output_dir: str
) -> None:
    """实现数据模型

    Args:
        service: 目标服务名称
        model_name: 模型名称
        table_name: 表名
        fields_file: 字段定义 JSON 文件路径
        output_dir: 输出目录
    """
    # 加载字段定义
    try:
        with open(fields_file, "r") as f:
            fields_data = json.load(f)
    except FileNotFoundError:
        click.echo(f"错误：字段定义文件 {fields_file} 不存在", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        click.echo(f"错误：字段定义文件 {fields_file} 格式错误", err=True)
        sys.exit(1)

    # 创建数据结构
    data_structure = DataStructure(
        model_name=model_name,
        table_name=table_name,
        fields=fields_data.get("fields", []),
        constraints=fields_data.get("constraints", []),
        indexes=fields_data.get("indexes", []),
    )

    # 执行模型实现
    agent = BackendAgent(service_root=output_dir)
    result = agent.implement_data_model(data_structure)

    # 输出结果
    click.echo(f"\n✓ 数据模型实现完成")
    click.echo(f"  模型名称: {result['model_name']}")
    click.echo(f"  表名: {result['table_name']}")
    click.echo(f"  字段数量: {result['fields_count']}")
    click.echo(f"  文件路径: {result['file_path']}")

    # 输出代码
    output_file = Path(output_dir) / service / result["file_path"]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(result["model_code"])
    click.echo(f"  代码已写入: {output_file}")


@cli.command()
@click.option("--service", required=True, help="目标服务名称")
@click.option("--model-name", required=True, help="模型名称")
@click.option("--endpoint", required=True, help="API 路径")
@click.option("--method", default="GET", help="HTTP 方法")
@click.option("--scope", default=None, help="权限 scope")
@click.option("--output-dir", default=".", help="输出目录")
def implement_route(
    service: str,
    model_name: str,
    endpoint: str,
    method: str,
    scope: str | None,
    output_dir: str,
) -> None:
    """实现 API 路由

    Args:
        service: 目标服务名称
        model_name: 模型名称
        endpoint: API 路径
        method: HTTP 方法
        scope: 权限 scope
        output_dir: 输出目录
    """
    # 创建 API 规范
    from .input_schemas import APISpec

    api_spec = APISpec(
        endpoint=endpoint,
        method=method,
        scope=scope,
        request={"name": f"{model_name}Request", "fields": []},
        response={"name": f"{model_name}Response", "fields": []},
    )

    # 执行路由实现
    agent = BackendAgent(service_root=output_dir)
    result = agent.implement_routes(service, [api_spec], model_name)

    # 输出结果
    click.echo(f"\n✓ API 路由实现完成")
    click.echo(f"  端点: {endpoint}")
    click.echo(f"  方法: {method}")
    click.echo(f"  文件路径: {result['file_path']}")

    # 输出代码
    output_file = Path(output_dir) / service / result["file_path"]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "a") as f:
        f.write(result["routes_code"])
    click.echo(f"  代码已追加到: {output_file}")


@cli.command()
@click.option("--service", required=True, help="目标服务名称")
@click.option("--model-name", required=True, help="模型名称")
@click.option("--output-dir", default=".", help="输出目录")
def generate_test(service: str, model_name: str, output_dir: str) -> None:
    """生成测试用例

    Args:
        service: 目标服务名称
        model_name: 模型名称
        output_dir: 输出目录
    """
    # 执行测试生成
    agent = BackendAgent(service_root=output_dir)
    result = agent.write_tests(model_name, service)

    # 输出结果
    click.echo(f"\n✓ 测试用例生成完成")
    click.echo(f"  测试文件: {result['test_file']}")
    click.echo(f"  测试数量: {result['test_count']}")
    click.echo(f"  文件路径: {result['file_path']}")

    # 输出代码
    output_file = Path(output_dir) / service / result["file_path"]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(result["test_code"])
    click.echo(f"  代码已写入: {output_file}")


@cli.command()
@click.option("--input-file", required=True, help="输入 JSON 文件路径")
@click.option("--output-dir", default=".", help="输出目录")
@click.option("--verbose", is_flag=True, help="详细输出")
def run_workflow(input_file: str, output_dir: str, verbose: bool) -> None:
    """运行完整工作流

    Args:
        input_file: 输入 JSON 文件路径
        output_dir: 输出目录
        verbose: 详细输出模式
    """
    # 加载输入数据
    try:
        with open(input_file, "r") as f:
            input_data_raw = json.load(f)
    except FileNotFoundError:
        click.echo(f"错误：输入文件 {input_file} 不存在", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        click.echo(f"错误：输入文件 {input_file} 格式错误", err=True)
        sys.exit(1)

    # 构建输入数据结构
    try:
        design_task = DesignTask(**input_data_raw.get("design_task", {}))

        data_structures = []
        for ds in input_data_raw.get("data_structures", []):
            data_structures.append(DataStructure(**ds))

        existing_code = None
        if input_data_raw.get("existing_code"):
            existing_code = ExistingCode(**input_data_raw["existing_code"])

        input_data = BackendAgentInput(
            design_task=design_task,
            data_structures=data_structures,
            existing_code=existing_code,
            context=input_data_raw.get("context", {}),
        )
    except Exception as e:
        click.echo(f"错误：输入数据解析失败 - {e}", err=True)
        sys.exit(1)

    # 运行工作流
    agent = BackendAgent(service_root=output_dir)
    result = agent.run_workflow(input_data)

    # 输出结果
    click.echo(f"\n{'='*60}")
    click.echo(f"Backend Agent 工作流执行完成")
    click.echo(f"{'='*60}")
    click.echo(f"\n任务信息:")
    click.echo(f"  设计ID: {result.implementation.design_id}")
    click.echo(f"  任务ID: {result.implementation.task_id}")
    click.echo(f"  服务: {result.implementation.service}")
    click.echo(f"  状态: {result.implementation.status}")

    click.echo(f"\n文件变更:")
    for file_info in result.implementation.files:
        click.echo(f"  [{file_info.type}] {file_info.path} - {file_info.description}")

    if result.test_result:
        click.echo(f"\n测试结果:")
        click.echo(f"  通过: {result.test_result.tests.passed}")
        click.echo(f"  失败: {result.test_result.tests.failed}")
        click.echo(f"  总数: {result.test_result.tests.total}")
        click.echo(f"  覆盖率: {result.test_result.tests.coverage}%")
        click.echo(f"  Lint: {'✓ 通过' if result.test_result.lint.passed else '✗ 失败'}")
        click.echo(
            f"  类型检查: {'✓ 通过' if result.test_result.typecheck.passed else '✗ 失败'}"
        )

    if result.errors:
        click.echo(f"\n错误 ({len(result.errors)} 个):")
        for error in result.errors:
            click.echo(f"  ✗ {error}")

    if result.warnings and verbose:
        click.echo(f"\n警告 ({len(result.warnings)} 个):")
        for warning in result.warnings:
            click.echo(f"  ⚠ {warning}")

    click.echo(f"\n下一步:")
    for step in result.next_steps:
        click.echo(f"  → {step}")

    click.echo(f"\n摘要: {result.summary}")
    click.echo(f"\n执行成功: {'✓ 是' if result.success else '✗ 否'}")

    # 输出详细结果到 JSON 文件
    output_json_file = Path(output_dir) / "backend_agent_output.json"
    with open(output_json_file, "w") as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    click.echo(f"\n详细结果已写入: {output_json_file}")


if __name__ == "__main__":
    cli()