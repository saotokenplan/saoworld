"""
Backend Agent 输入数据结构定义

定义 Backend Agent 从 System Designer Agent 接收的输入数据格式。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DesignTask(BaseModel):
    """设计任务输入"""

    model_config = ConfigDict(extra="forbid")

    design_id: str = Field(..., description="设计文档ID")
    task_id: str = Field(..., description="任务ID")
    title: str = Field(..., description="任务标题")
    type: str = Field(..., description="任务类型：api/model/repository/schema/test")
    target_service: str = Field(..., description="目标服务名称")
    requirements: list[str] = Field(..., description="需求列表")
    data_model: dict[str, Any] | None = Field(None, description="数据模型定义")
    priority: str = Field(default="medium", description="优先级：high/medium/low")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class APISpec(BaseModel):
    """API 规范输入"""

    model_config = ConfigDict(extra="forbid")

    endpoint: str = Field(..., description="API 路径")
    method: str = Field(..., description="HTTP 方法：GET/POST/PUT/DELETE")
    scope: str | None = Field(None, description="权限 scope")
    request: dict[str, Any] = Field(..., description="请求模型定义")
    response: dict[str, Any] = Field(..., description="响应模型定义")
    errors: list[dict[str, Any]] = Field(default_factory=list, description="错误定义列表")
    description: str | None = Field(None, description="接口描述")


class FieldDefinition(BaseModel):
    """字段定义"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="字段名")
    type: str = Field(..., description="字段类型")
    primary_key: bool = Field(default=False, description="是否为主键")
    nullable: bool = Field(default=True, description="是否可为空")
    default: Any | None = Field(None, description="默认值")
    server_default: str | None = Field(None, description="服务器默认值")
    onupdate: str | None = Field(None, description="更新时触发")
    check: list[str] | None = Field(None, description="CHECK 约束值列表")
    foreign_key: str | None = Field(None, description="外键引用")
    unique: bool = Field(default=False, description="是否唯一")
    index: bool = Field(default=False, description="是否建索引")


class ConstraintDefinition(BaseModel):
    """约束定义"""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="约束类型：UNIQUE/CHECK/FOREIGN_KEY")
    fields: list[str] = Field(..., description="约束字段列表")
    reference: str | None = Field(None, description="外键引用表")
    condition: str | None = Field(None, description="CHECK 条件")


class IndexDefinition(BaseModel):
    """索引定义"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="索引名")
    fields: list[str] = Field(..., description="索引字段列表")
    unique: bool = Field(default=False, description="是否唯一索引")


class DataStructure(BaseModel):
    """数据结构输入"""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="模型名称")
    table_name: str = Field(..., description="表名")
    fields: list[FieldDefinition] = Field(..., description="字段定义列表")
    constraints: list[ConstraintDefinition] = Field(default_factory=list, description="约束列表")
    indexes: list[IndexDefinition] = Field(default_factory=list, description="索引列表")
    relationships: list[dict[str, Any]] = Field(default_factory=list, description="关系定义列表")


class ExistingCode(BaseModel):
    """现有代码状态"""

    model_config = ConfigDict(extra="forbid")

    service_name: str = Field(..., description="服务名称")
    has_routes: bool = Field(default=False, description="是否存在路由文件")
    has_models: bool = Field(default=False, description="是否存在模型文件")
    has_repositories: bool = Field(default=False, description="是否存在仓库文件")
    has_schemas: bool = Field(default=False, description="是否存在 schema 文件")
    has_tests: bool = Field(default=False, description="是否存在测试文件")
    existing_models: list[str] = Field(default_factory=list, description="已有模型名称")
    existing_routes: list[str] = Field(default_factory=list, description="已有路由路径")
    test_count: int = Field(default=0, description="已有测试数量")


class BackendAgentInput(BaseModel):
    """Backend Agent 完整输入"""

    model_config = ConfigDict(extra="forbid")

    design_task: DesignTask = Field(..., description="设计任务")
    api_specs: list[APISpec] = Field(default_factory=list, description="API 规范列表")
    data_structures: list[DataStructure] = Field(default_factory=list, description="数据结构列表")
    existing_code: ExistingCode | None = Field(None, description="现有代码状态")
    context: dict[str, Any] = Field(default_factory=dict, description="额外上下文信息")
