from pydantic import BaseModel, Field
from typing import List, Optional


class CodeChange(BaseModel):
    path: str = Field(description="文件路径")
    type: str = Field(description="变更类型：new/modified/deleted")
    diff: Optional[str] = Field(default=None, description="变更差异")
    commit_hash: Optional[str] = Field(default=None, description="提交哈希")


class CodeChanges(BaseModel):
    changes: List[CodeChange] = Field(description="代码变更列表")


class ScenarioStep(BaseModel):
    action: Optional[str] = Field(default=None, description="操作步骤")
    data: Optional[dict] = Field(default=None, description="请求数据")
    expected: Optional[str] = Field(default=None, description="预期结果")


class AcceptanceScenario(BaseModel):
    id: str = Field(description="场景ID")
    description: str = Field(description="场景描述")
    steps: List[ScenarioStep] = Field(description="测试步骤")


class AcceptanceCase(BaseModel):
    acceptance_id: str = Field(description="验收用例ID")
    task_id: str = Field(description="关联任务ID")
    title: str = Field(description="验收用例标题")
    scenarios: List[AcceptanceScenario] = Field(description="验收场景列表")


class TestTask(BaseModel):
    test_task_id: str = Field(description="测试任务ID")
    design_id: Optional[str] = Field(default=None, description="设计文档ID")
    task_id: str = Field(description="关联任务ID")
    title: str = Field(description="测试任务标题")
    target_service: str = Field(description="目标服务")
    test_type: str = Field(description="测试类型：unit/integration/e2e")
    requirements: List[str] = Field(description="测试需求列表")
    code_changes: List[CodeChange] = Field(description="代码变更列表")


class DesignDocument(BaseModel):
    design_id: str = Field(description="设计文档ID")
    title: str = Field(description="设计文档标题")
    content: str = Field(description="设计文档内容")
    target_service: str = Field(description="目标服务")
