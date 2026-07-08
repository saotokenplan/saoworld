from ..build_agent import BuildAgent
from ..input_schemas import (
    BuildTask, BuildConfig, VersionConfig,
    ClientBuildConfig, ServerBuildConfig,
    GrayScope, ChangelogEntry
)


def test_check_code_branch():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="测试构建",
        type="full",
        branch="feature/test-branch",
        version="0.1.0",
        components=["client", "server", "content"],
    )
    result = agent.check_code_branch(build_task)
    assert result["branch"] == "feature/test-branch"
    assert result["exists"] is True
    assert result["clean"] is True
    assert result["gate_passed"] is True
    assert "commit_hash" in result


def test_build_client():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="客户端构建测试",
        type="client",
        branch="main",
        version="0.1.0",
        components=["client"],
    )
    build_config = BuildConfig(
        client=ClientBuildConfig(
            platforms=["windows", "linux"],
            build_type="release",
            output_dir="build/client"
        )
    )
    result = agent.build_client(build_task, build_config)
    assert result.status == "success"
    assert len(result.platforms) == 2
    assert "windows" in result.platforms
    assert "linux" in result.platforms
    assert len(result.files) == 2
    assert result.size == "150MB"


def test_build_server_images():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="服务端构建测试",
        type="server",
        branch="main",
        version="0.2.0",
        components=["server"],
    )
    build_config = BuildConfig(
        server=ServerBuildConfig(
            services=["vote", "world", "content"],
            docker_registry="registry.example.com"
        )
    )
    result = agent.build_server_images(build_task, build_config)
    assert result.status == "success"
    assert len(result.services) == 3
    assert len(result.images) == 3
    assert result.images[0].name == "vote-service"
    assert result.images[0].tag == "0.2.0"
    assert result.registry == "registry.example.com"


def test_package_content_with_packages():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="内容包打包测试",
        type="content",
        branch="main",
        version="0.1.0",
        components=["content"],
        content_packages=["pkg_test_001", "pkg_test_002"],
    )
    result = agent.package_content(build_task)
    assert result.status == "success"
    assert len(result.packages) == 2
    assert "pkg_test_001.zip" in result.packages[0]


def test_package_content_empty():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="空内容包测试",
        type="content",
        branch="main",
        version="0.1.0",
        components=["content"],
        content_packages=[],
    )
    result = agent.package_content(build_task)
    assert result.status == "success"
    assert len(result.packages) == 0


def test_generate_rollback_package():
    from ..output_schemas import (
        BuildOutput, ComponentBuildResult,
        ClientBuildResult, ServerBuildResult, ContentBuildResult
    )
    agent = BuildAgent()
    components = ComponentBuildResult(
        client=ClientBuildResult(status="success", platforms=[], files=[], size="0MB"),
        server=ServerBuildResult(status="success", services=[], images=[], registry=None),
        content=ContentBuildResult(status="success", packages=[], size="0MB"),
    )
    build_output = BuildOutput(
        build_id="BUILD-001",
        version="0.2.0",
        build_number=1,
        timestamp="2026-07-08T10:00:00Z",
        status="success",
        components=components,
    )
    rollback_path = agent.generate_rollback_package(build_output)
    assert "0.2.0-rollback.zip" in rollback_path
    assert "build/rollback/" in rollback_path


def test_write_version_metadata():
    from ..output_schemas import (
        BuildOutput, ComponentBuildResult,
        ClientBuildResult, ServerBuildResult, ContentBuildResult
    )
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="版本元数据测试",
        type="full",
        branch="main",
        version="0.2.0",
        components=["client", "server", "content"],
    )
    version_config = VersionConfig(
        version="0.2.0",
        build_number=1,
        changelog=[
            ChangelogEntry(type="feature", description="新增测试功能", component="client"),
            ChangelogEntry(type="bugfix", description="修复投票问题", component="vote"),
        ],
        dependencies={"python": ">=3.11", "fastapi": ">=0.111"},
    )
    components = ComponentBuildResult(
        client=ClientBuildResult(status="success", platforms=[], files=[], size="0MB"),
        server=ServerBuildResult(status="success", services=[], images=[], registry=None),
        content=ContentBuildResult(status="success", packages=[], size="0MB"),
    )
    build_output = BuildOutput(
        build_id="BUILD-001",
        version="0.2.0",
        build_number=1,
        timestamp="2026-07-08T10:00:00Z",
        status="success",
        components=components,
        rollback_package="build/rollback/0.2.0-rollback.zip",
    )
    result = agent.write_version_metadata(build_task, version_config, build_output)
    assert result.version == "0.2.0"
    assert result.build_id == "BUILD-001"
    assert result.status == "packaged"
    assert len(result.changelog) == 2
    assert len(result.components) == 3
    assert result.rollback_package is not None
    assert result.version_id.startswith("VER-")


def test_generate_build_report():
    from ..output_schemas import (
        BuildOutput, ComponentBuildResult,
        ClientBuildResult, ServerBuildResult, ContentBuildResult
    )
    agent = BuildAgent()
    components = ComponentBuildResult(
        client=ClientBuildResult(status="success", platforms=["windows"], files=["game.exe"], size="150MB"),
        server=ServerBuildResult(status="success", services=["vote"], images=[], registry=None),
        content=ContentBuildResult(status="success", packages=["pkg.zip"], size="5MB"),
    )
    build_output = BuildOutput(
        build_id="BUILD-001",
        version="0.2.0",
        build_number=1,
        timestamp="2026-07-08T10:00:00Z",
        status="success",
        components=components,
        rollback_package="build/rollback/0.2.0-rollback.zip",
    )
    report = agent.generate_build_report(build_output)
    assert report.build_id == "BUILD-001"
    assert report.report_id.startswith("REPORT-")
    assert report.summary.overall_status == "success"
    assert report.summary.total_components == 3
    assert report.summary.success_components == 3
    assert report.summary.failed_components == 0
    assert "client_build" in report.results
    assert "server_build" in report.results
    assert "content_packaging" in report.results
    assert "rollback_generation" in report.results


def test_deploy_to_gray():
    from ..output_schemas import (
        BuildOutput, ComponentBuildResult,
        ClientBuildResult, ServerBuildResult, ContentBuildResult
    )
    agent = BuildAgent()
    components = ComponentBuildResult(
        client=ClientBuildResult(status="success", platforms=[], files=[], size="0MB"),
        server=ServerBuildResult(status="success", services=[], images=[], registry=None),
        content=ContentBuildResult(status="success", packages=[], size="0MB"),
    )
    build_output = BuildOutput(
        build_id="BUILD-001",
        version="0.2.0",
        build_number=1,
        timestamp="2026-07-08T10:00:00Z",
        status="success",
        components=components,
    )
    gray_scope = GrayScope(
        region_ids=["region_test_01"],
        player_percent=10,
        player_ids=[],
    )
    result = agent.deploy_to_gray(build_output, gray_scope)
    assert result["deployed"] is True
    assert result["environment"] == "staging"
    assert result["status"] == "gray"
    assert result["gray_scope"]["region_ids"] == ["region_test_01"]
    assert result["gray_scope"]["player_percent"] == 10


def test_execute_build_workflow_full():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-001",
        task_id="TASK-001",
        title="完整构建工作流测试",
        type="full",
        branch="main",
        version="0.2.0",
        components=["client", "server", "content"],
        content_packages=["pkg_test_001"],
    )
    version_config = VersionConfig(
        version="0.2.0",
        build_number=1,
        changelog=[ChangelogEntry(type="feature", description="测试功能")],
    )
    result = agent.execute_build_workflow(build_task, version_config=version_config)
    assert result.success is True
    assert result.build_output is not None
    assert result.report is not None
    assert result.version_metadata is not None
    assert result.build_output.version == "0.2.0"
    assert result.report.summary.overall_status == "success"
    assert "构建流程执行完成" in result.message


def test_execute_build_workflow_gray_deploy():
    agent = BuildAgent()
    build_task = BuildTask(
        build_task_id="BUILD-GRAY-001",
        task_id="TASK-001",
        title="灰度发布构建测试",
        type="full",
        branch="main",
        version="0.2.0",
        components=["client", "server", "content"],
        content_packages=["pkg_gray_001"],
        gray_scope=GrayScope(
            region_ids=["region_gray_01"],
            player_percent=10,
        ),
        target_environment="staging",
    )
    version_config = VersionConfig(
        version="0.2.0",
        build_number=1,
        changelog=[ChangelogEntry(type="feature", description="灰度测试功能")],
    )
    result = agent.execute_build_workflow(build_task, version_config=version_config)
    assert result.success is True
    assert result.version_metadata is not None
    assert result.version_metadata.status == "gray"


def test_error_handler_build_failure():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("build_failure", "客户端构建失败")


def test_error_handler_image_push_failure():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("image_push_failure", "Docker镜像推送失败")


def test_error_handler_missing_content():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("missing_content", "内容包不存在")


def test_error_handler_rollback_failure():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("rollback_failure", "回滚包生成失败")


def test_error_handler_resource_insufficient():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("resource_insufficient", "磁盘空间不足")


def test_error_handler_workflow_error():
    from ..error_handler import BuildErrorHandler
    handler = BuildErrorHandler()
    handler.handle_error("workflow", "工作流执行异常")
