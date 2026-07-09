import argparse
import json
from .build_agent import BuildAgent
from .build_input_schemas import BuildTask, BuildConfig, VersionConfig, ChangelogEntry


def main():
    parser = argparse.ArgumentParser(description="Build Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    build_client_parser = subparsers.add_parser("build-client", help="构建客户端")
    build_client_parser.add_argument("--version", required=True, help="版本号")
    build_client_parser.add_argument("--branch", default="main", help="代码分支")
    build_client_parser.add_argument("--platform", action="append", default=None, help="目标平台")

    build_server_parser = subparsers.add_parser("build-server", help="构建服务端镜像")
    build_server_parser.add_argument("--version", required=True, help="版本号")
    build_server_parser.add_argument("--branch", default="main", help="代码分支")
    build_server_parser.add_argument("--service", action="append", default=None, help="要构建的服务")

    package_content_parser = subparsers.add_parser("package-content", help="打包内容包")
    package_content_parser.add_argument("--version", required=True, help="版本号")
    package_content_parser.add_argument("--package", action="append", default=None, help="内容包名称")

    workflow_parser = subparsers.add_parser("run-workflow", help="运行完整构建工作流")
    workflow_parser.add_argument("--task-id", required=True, help="构建任务ID")
    workflow_parser.add_argument("--version", required=True, help="版本号")
    workflow_parser.add_argument("--branch", default="main", help="代码分支")
    workflow_parser.add_argument("--component", action="append", required=True, help="构建组件")
    workflow_parser.add_argument("--type", default="full", help="构建类型")
    workflow_parser.add_argument("--title", default="自动构建任务", help="构建任务标题")

    args = parser.parse_args()
    agent = BuildAgent()

    if args.command == "build-client":
        build_task = BuildTask(
            build_task_id=f"BUILD-CLIENT-{args.version}",
            task_id="TASK-001",
            title=f"客户端构建 {args.version}",
            type="client",
            branch=args.branch,
            version=args.version,
            components=["client"],
        )
        build_config = BuildConfig()
        if args.platform:
            build_config.client.platforms = args.platform
        result = agent.build_client(build_task, build_config)
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "build-server":
        build_task = BuildTask(
            build_task_id=f"BUILD-SERVER-{args.version}",
            task_id="TASK-001",
            title=f"服务端构建 {args.version}",
            type="server",
            branch=args.branch,
            version=args.version,
            components=["server"],
        )
        build_config = BuildConfig()
        if args.service:
            build_config.server.services = args.service
        result = agent.build_server_images(build_task, build_config)
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "package-content":
        build_task = BuildTask(
            build_task_id=f"PACKAGE-CONTENT-{args.version}",
            task_id="TASK-001",
            title=f"内容包打包 {args.version}",
            type="content",
            branch="main",
            version=args.version,
            components=["content"],
            content_packages=args.package or [],
        )
        result = agent.package_content(build_task)
        print(json.dumps(result.model_dump(), indent=2))

    elif args.command == "run-workflow":
        build_task = BuildTask(
            build_task_id=args.task_id,
            task_id="TASK-001",
            title=args.title,
            type=args.type,
            branch=args.branch,
            version=args.version,
            components=args.component,
        )
        version_config = VersionConfig(
            version=args.version,
            build_number=1,
            changelog=[ChangelogEntry(type="feature", description="自动构建")]
        )
        result = agent.execute_build_workflow(build_task, version_config=version_config)
        print(json.dumps(result.model_dump(), indent=2, default=str))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
