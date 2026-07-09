from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ClientBuildResult(BaseModel):
    status: str = Field(description="构建状态：success/failed")
    platforms: List[str] = Field(default_factory=list, description="构建的平台列表")
    files: List[str] = Field(default_factory=list, description="构建产物文件列表")
    size: Optional[str] = Field(default=None, description="总大小")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class DockerImage(BaseModel):
    name: str = Field(description="镜像名称")
    tag: str = Field(description="镜像标签")
    registry: Optional[str] = Field(default=None, description="镜像仓库")


class ServerBuildResult(BaseModel):
    status: str = Field(description="构建状态：success/failed")
    services: List[str] = Field(default_factory=list, description="构建的服务列表")
    images: List[DockerImage] = Field(default_factory=list, description="Docker镜像列表")
    registry: Optional[str] = Field(default=None, description="镜像仓库")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class ContentBuildResult(BaseModel):
    status: str = Field(description="构建状态：success/failed")
    packages: List[str] = Field(default_factory=list, description="内容包文件列表")
    size: Optional[str] = Field(default=None, description="总大小")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class ComponentBuildResult(BaseModel):
    client: ClientBuildResult = Field(description="客户端构建结果")
    server: ServerBuildResult = Field(description="服务端构建结果")
    content: ContentBuildResult = Field(description="内容构建结果")


class BuildOutput(BaseModel):
    build_id: str = Field(description="构建ID")
    version: str = Field(description="版本号")
    build_number: int = Field(description="构建号")
    timestamp: str = Field(description="构建时间戳")
    status: str = Field(description="构建状态：success/failed")
    components: ComponentBuildResult = Field(description="各组件构建结果")
    rollback_package: Optional[str] = Field(default=None, description="回滚包路径")
    git_commit: Optional[str] = Field(default=None, description="Git提交哈希")
    built_by: str = Field(default="build-agent", description="构建者")


class BuildResultSummary(BaseModel):
    overall_status: str = Field(description="总体状态：success/failed")
    total_components: int = Field(description="组件总数")
    success_components: int = Field(description="成功组件数")
    failed_components: int = Field(description="失败组件数")
    total_duration: str = Field(description="总耗时")


class BuildReport(BaseModel):
    report_id: str = Field(description="报告ID")
    build_id: str = Field(description="构建ID")
    timestamp: str = Field(description="生成时间")
    results: Dict[str, Dict] = Field(description="各组件构建结果详情")
    summary: BuildResultSummary = Field(description="构建摘要")


class VersionMetadata(BaseModel):
    version_id: str = Field(description="版本记录ID")
    version: str = Field(description="版本号")
    build_id: str = Field(description="构建ID")
    release_date: str = Field(description="发布日期")
    status: str = Field(description="版本状态：packaged/gray/live/archived/rolled_back")
    changelog: List[Dict] = Field(default_factory=list, description="变更日志")
    components: List[str] = Field(default_factory=list, description="包含的组件")
    rollback_package: Optional[str] = Field(default=None, description="回滚包路径")
    created_at: str = Field(description="创建时间")


class BuildResult(BaseModel):
    success: bool = Field(description="是否成功")
    build_output: Optional[BuildOutput] = Field(default=None, description="构建输出")
    report: Optional[BuildReport] = Field(default=None, description="构建报告")
    version_metadata: Optional[VersionMetadata] = Field(default=None, description="版本元数据")
    message: str = Field(description="结果消息")
