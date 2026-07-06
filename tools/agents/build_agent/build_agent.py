import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from .input_schemas import BuildTask, VersionConfig, BuildConfig, GrayScope, ChangelogEntry
from .output_schemas import (
    BuildOutput, BuildReport, VersionMetadata, ComponentBuildResult,
    ClientBuildResult, ServerBuildResult, ContentBuildResult,
    DockerImage, BuildResultSummary, BuildResult
)
from .error_handler import BuildErrorHandler


class BuildAgent:
    def __init__(self):
        self.error_handler = BuildErrorHandler()

    def check_code_branch(
        self,
        build_task: BuildTask,
    ) -> Dict:
        result = {
            "branch": build_task.branch,
            "exists": True,
            "clean": True,
            "gate_passed": True,
            "commit_hash": f"abc{uuid.uuid4().hex[:9]}",
        }
        return result

    def build_client(
        self,
        build_task: BuildTask,
        build_config: Optional[BuildConfig] = None,
    ) -> ClientBuildResult:
        config = build_config or BuildConfig()
        client_config = config.client
        files = []
        for platform in client_config.platforms:
            ext = ".exe" if platform == "windows" else ".zip"
            filename = f"{client_config.output_dir}/game-{platform}{ext}"
            files.append(filename)
        return ClientBuildResult(
            status="success",
            platforms=client_config.platforms,
            files=files,
            size="150MB",
            errors=[]
        )

    def build_server_images(
        self,
        build_task: BuildTask,
        build_config: Optional[BuildConfig] = None,
    ) -> ServerBuildResult:
        config = build_config or BuildConfig()
        server_config = config.server
        images = []
        for service in server_config.services:
            image = DockerImage(
                name=f"{service}-service",
                tag=build_task.version,
                registry=server_config.docker_registry
            )
            images.append(image)
        return ServerBuildResult(
            status="success",
            services=server_config.services,
            images=images,
            registry=server_config.docker_registry,
            errors=[]
        )

    def package_content(
        self,
        build_task: BuildTask,
        build_config: Optional[BuildConfig] = None,
    ) -> ContentBuildResult:
        config = build_config or BuildConfig()
        content_config = config.content
        packages = []
        if build_task.content_packages:
            for pkg in build_task.content_packages:
                pkg_path = f"{content_config.output_dir}/{pkg}.zip"
                packages.append(pkg_path)
        status = "success" if packages else "success"
        return ContentBuildResult(
            status=status,
            packages=packages,
            size="5MB" if packages else "0MB",
            errors=[]
        )

    def generate_rollback_package(
        self,
        build_output: BuildOutput,
    ) -> str:
        rollback_path = f"build/rollback/{build_output.version}-rollback.zip"
        return rollback_path

    def write_version_metadata(
        self,
        build_task: BuildTask,
        version_config: VersionConfig,
        build_output: BuildOutput,
    ) -> VersionMetadata:
        changelog_dicts = [
            {"type": entry.type, "description": entry.description, "component": entry.component}
            for entry in version_config.changelog
        ]
        return VersionMetadata(
            version_id=f"VER-{uuid.uuid4().hex[:8]}",
            version=build_task.version,
            build_id=build_output.build_id,
            release_date=datetime.now(timezone.utc).isoformat(),
            status="packaged",
            changelog=changelog_dicts,
            components=build_task.components,
            rollback_package=build_output.rollback_package,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def generate_build_report(
        self,
        build_output: BuildOutput,
    ) -> BuildReport:
        results = {
            "client_build": {
                "status": build_output.components.client.status,
                "platforms": build_output.components.client.platforms,
                "errors": build_output.components.client.errors,
            },
            "server_build": {
                "status": build_output.components.server.status,
                "services": build_output.components.server.services,
                "errors": build_output.components.server.errors,
            },
            "content_packaging": {
                "status": build_output.components.content.status,
                "packages": build_output.components.content.packages,
                "errors": build_output.components.content.errors,
            },
            "rollback_generation": {
                "status": "success" if build_output.rollback_package else "failed",
                "package": build_output.rollback_package,
            },
        }
        success_count = 0
        if build_output.components.client.status == "success":
            success_count += 1
        if build_output.components.server.status == "success":
            success_count += 1
        if build_output.components.content.status == "success":
            success_count += 1
        overall_status = "success" if success_count == 3 else "failed"
        summary = BuildResultSummary(
            overall_status=overall_status,
            total_components=3,
            success_components=success_count,
            failed_components=3 - success_count,
            total_duration="28m"
        )
        return BuildReport(
            report_id=f"REPORT-{uuid.uuid4().hex[:8]}",
            build_id=build_output.build_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            results=results,
            summary=summary
        )

    def deploy_to_gray(
        self,
        build_output: BuildOutput,
        gray_scope: GrayScope,
    ) -> Dict:
        result = {
            "deployed": True,
            "environment": "staging",
            "gray_scope": {
                "region_ids": gray_scope.region_ids,
                "player_percent": gray_scope.player_percent,
                "player_ids": gray_scope.player_ids,
            },
            "version": build_output.version,
            "status": "gray",
        }
        return result

    def execute_build_workflow(
        self,
        build_task: BuildTask,
        build_config: Optional[BuildConfig] = None,
        version_config: Optional[VersionConfig] = None,
    ) -> BuildResult:
        try:
            branch_info = self.check_code_branch(build_task)

            client_result = None
            server_result = None
            content_result = None

            if "client" in build_task.components:
                client_result = self.build_client(build_task, build_config)
            else:
                client_result = ClientBuildResult(
                    status="skipped",
                    platforms=[],
                    files=[],
                    size="0MB",
                    errors=[]
                )

            if "server" in build_task.components:
                server_result = self.build_server_images(build_task, build_config)
            else:
                server_result = ServerBuildResult(
                    status="skipped",
                    services=[],
                    images=[],
                    registry=None,
                    errors=[]
                )

            if "content" in build_task.components:
                content_result = self.package_content(build_task, build_config)
            else:
                content_result = ContentBuildResult(
                    status="skipped",
                    packages=[],
                    size="0MB",
                    errors=[]
                )

            components = ComponentBuildResult(
                client=client_result,
                server=server_result,
                content=content_result
            )

            build_number = version_config.build_number if version_config else 1
            build_output = BuildOutput(
                build_id=f"BUILD-{uuid.uuid4().hex[:8]}",
                version=build_task.version,
                build_number=build_number,
                timestamp=datetime.now(timezone.utc).isoformat(),
                status="success",
                components=components,
                git_commit=branch_info.get("commit_hash"),
                built_by="build-agent"
            )

            rollback_path = self.generate_rollback_package(build_output)
            build_output.rollback_package = rollback_path

            version_meta = None
            if version_config:
                version_meta = self.write_version_metadata(build_task, version_config, build_output)

            report = self.generate_build_report(build_output)

            if build_task.gray_scope and build_task.target_environment == "staging":
                self.deploy_to_gray(build_output, build_task.gray_scope)
                if version_meta:
                    version_meta.status = "gray"

            success = report.summary.overall_status == "success"
            return BuildResult(
                success=success,
                build_output=build_output,
                report=report,
                version_metadata=version_meta,
                message="构建流程执行完成"
            )
        except Exception as e:
            self.error_handler.handle_error("workflow", str(e))
            return BuildResult(
                success=False,
                build_output=None,
                report=None,
                version_metadata=None,
                message=f"构建流程执行失败: {str(e)}"
            )
