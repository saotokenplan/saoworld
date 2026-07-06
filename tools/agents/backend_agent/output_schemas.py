"""
Backend Agent 输出数据结构定义

定义 Backend Agent 输出给 QA Agent 和版本控制的产物格式。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FileInfo(BaseModel):
    """文件信息"""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="文件路径")
    type: str = Field(..., description="文件类型：new/modified/deleted")
    description: str = Field(..., description="变更描述")
    lines_added: int = Field(default=0, description="新增行数")
    lines_removed: int = Field(default=0, description="删除行数")


class TestStatistics(BaseModel):
    """测试统计"""

    model_config = ConfigDict(extra="forbid")

    passed: int = Field(..., description="通过测试数")
    failed: int = Field(..., description="失败测试数")
    total: int = Field(..., description="总测试数")
    coverage: float = Field(default=0.0, description="测试覆盖率百分比")


class LintResult(BaseModel):
    """Lint 检查结果"""

    model_config = ConfigDict(extra="forbid")

    passed: bool = Field(..., description="是否通过")
    errors: list[str] = Field(default_factory=list, description="错误列表")
    warnings: list[str] = Field(default_factory=list, description="警告列表")


class TypeCheckResult(BaseModel):
    """类型检查结果"""

    model_config = ConfigDict(extra="forbid")

    passed: bool = Field(..., description="是否通过")
    errors: list[str] = Field(default_factory=list, description="错误列表")


class TestResult(BaseModel):
    """测试结果"""

    model_config = ConfigDict(extra="forbid")

    service: str = Field(..., description="服务名称")
    tests: TestStatistics = Field(..., description="测试统计")
    lint: LintResult = Field(..., description="Lint 检查结果")
    typecheck: TypeCheckResult = Field(..., description="类型检查结果")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")


class ImplementationOutput(BaseModel):
    """实现输出元数据"""

    model_config = ConfigDict(extra="forbid")

    implementation_id: str = Field(..., description="实现ID")
    design_id: str = Field(..., description="设计ID")
    task_id: str = Field(..., description="任务ID")
    service: str = Field(..., description="服务名称")
    files: list[FileInfo] = Field(..., description="文件变更列表")
    version: str = Field(default="1.0", description="版本号")
    status: str = Field(..., description="状态：completed/failed/in_progress")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    notes: list[str] = Field(default_factory=list, description="实现备注")


class BackendResult(BaseModel):
    """Backend Agent 完整输出"""

    model_config = ConfigDict(extra="forbid")

    implementation: ImplementationOutput = Field(..., description="实现输出")
    test_result: TestResult | None = Field(None, description="测试结果")
    errors: list[str] = Field(default_factory=list, description="错误列表")
    warnings: list[str] = Field(default_factory=list, description="警告列表")
    next_steps: list[str] = Field(default_factory=list, description="下一步建议")
    success: bool = Field(..., description="是否成功")
    summary: str = Field(..., description="执行摘要")