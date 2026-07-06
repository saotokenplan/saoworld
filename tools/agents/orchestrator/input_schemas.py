from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class Milestone(BaseModel):
    id: str = Field(description="里程碑ID")
    name: str = Field(description="里程碑名称")
    due_date: str = Field(description="截止日期")


class TaskInput(BaseModel):
    id: str = Field(description="任务ID")
    title: str = Field(description="任务标题")
    priority: str = Field(description="优先级：P0/P1/P2/P3")
    assignee: str = Field(description="指派代理")
    type: str = Field(description="任务类型：design/implementation/test/build/ops")
    inputs: List[str] = Field(default_factory=list, description="输入文件列表")
    outputs: List[str] = Field(default_factory=list, description="输出文件列表")
    dependencies: List[str] = Field(default_factory=list, description="依赖任务ID列表")
    status: str = Field(default="pending", description="任务状态：pending/in_progress/completed/failed")


class VersionBrief(BaseModel):
    version_brief_id: str = Field(description="版本简报ID")
    version: str = Field(description="版本号")
    objectives: List[str] = Field(description="版本目标列表")
    milestones: List[Milestone] = Field(description="里程碑列表")
    tasks: List[TaskInput] = Field(description="任务列表")


class GateResult(BaseModel):
    status: str = Field(description="门禁状态：pass/fail")
    timestamp: str = Field(description="检查时间戳")


class ServiceGateResults(BaseModel):
    lint: GateResult = Field(description="静态检查")
    typecheck: GateResult = Field(description="类型检查")
    tests: GateResult = Field(description="测试检查")


class GateResults(BaseModel):
    gate_results: Dict[str, ServiceGateResults] = Field(description="各服务门禁结果")


class AgentStatusItem(BaseModel):
    status: str = Field(description="代理状态：idle/busy/running")
    current_task: Optional[str] = Field(default=None, description="当前任务ID")


class AgentStatus(BaseModel):
    agent_status: Dict[str, AgentStatusItem] = Field(description="各代理状态")


class TaskDefinition(BaseModel):
    task_id: str = Field(description="任务ID")
    title: str = Field(description="任务标题")
    type: str = Field(description="任务类型")
    agent: str = Field(description="指派代理")
    inputs: List[str] = Field(default_factory=list, description="输入文件")
    outputs: List[str] = Field(default_factory=list, description="输出文件")
    dependencies: List[str] = Field(default_factory=list, description="依赖任务ID")
    status: str = Field(default="pending", description="任务状态")