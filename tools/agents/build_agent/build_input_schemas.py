from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class GrayScope(BaseModel):
    region_ids: List[str] = Field(default_factory=list, description="灰度区域ID列表")
    player_percent: int = Field(default=0, ge=0, le=100, description="灰度玩家百分比")
    player_ids: List[str] = Field(default_factory=list, description="灰度玩家ID白名单")


class ChangelogEntry(BaseModel):
    type: str = Field(description="变更类型：feature/bugfix/refactor/docs")
    description: str = Field(description="变更描述")
    component: Optional[str] = Field(default=None, description="关联组件")


class BuildTask(BaseModel):
    build_task_id: str = Field(description="构建任务ID")
    task_id: str = Field(description="关联任务ID")
    title: str = Field(description="构建任务标题")
    type: str = Field(description="构建类型：full/client/server/content")
    branch: str = Field(description="代码分支")
    version: str = Field(description="版本号")
    components: List[str] = Field(description="构建组件列表：client/server/content")
    content_packages: List[str] = Field(default_factory=list, description="内容包列表")
    gray_scope: Optional[GrayScope] = Field(default=None, description="灰度范围配置")
    target_environment: str = Field(default="staging", description="目标环境")


class VersionConfig(BaseModel):
    version: str = Field(description="版本号")
    build_number: int = Field(description="构建号")
    git_commit: Optional[str] = Field(default=None, description="Git提交哈希")
    timestamp: Optional[str] = Field(default=None, description="构建时间戳")
    changelog: List[ChangelogEntry] = Field(default_factory=list, description="变更日志")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="依赖版本")


class ClientBuildConfig(BaseModel):
    platforms: List[str] = Field(default_factory=lambda: ["windows", "linux", "mac"], description="目标平台")
    build_type: str = Field(default="release", description="构建类型：release/debug")
    export_presets: str = Field(default="presets.cfg", description="导出配置文件")
    output_dir: str = Field(default="build/client", description="输出目录")


class ServerBuildConfig(BaseModel):
    services: List[str] = Field(
        default_factory=lambda: ["vote", "world", "content", "generation", "review", "player", "ops", "gateway"],
        description="服务列表"
    )
    docker_registry: str = Field(default="registry.example.com", description="Docker镜像仓库")
    build_args: Dict[str, str] = Field(default_factory=dict, description="构建参数")
    output_dir: str = Field(default="build/server", description="输出目录")


class ContentBuildConfig(BaseModel):
    packages: List[str] = Field(default_factory=list, description="内容包列表")
    output_dir: str = Field(default="build/content", description="输出目录")


class BuildConfig(BaseModel):
    client: ClientBuildConfig = Field(default_factory=ClientBuildConfig, description="客户端构建配置")
    server: ServerBuildConfig = Field(default_factory=ServerBuildConfig, description="服务端构建配置")
    content: ContentBuildConfig = Field(default_factory=ContentBuildConfig, description="内容构建配置")
