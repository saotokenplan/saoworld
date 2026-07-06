from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class SceneOutput(BaseModel):
    scene_id: str = Field(..., description="场景ID")
    design_id: str = Field(..., description="设计文档ID")
    task_id: str = Field(..., description="任务ID")
    file_path: str = Field(..., description="场景文件路径")
    script_path: str = Field(..., description="脚本文件路径")
    version: str = Field("1.0", description="版本号")
    status: str = Field("completed", description="状态")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")


class ScriptOutput(BaseModel):
    script_id: str = Field(..., description="脚本ID")
    file_path: str = Field(..., description="脚本文件路径")
    extends: str = Field(..., description="继承类")
    properties_count: int = Field(0, description="属性数量")
    methods_count: int = Field(0, description="方法数量")
    signals_count: int = Field(0, description="信号数量")
    status: str = Field("completed", description="状态")


class TestCase(BaseModel):
    name: str = Field(..., description="测试用例名称")
    description: str = Field(..., description="测试用例描述")
    expected_result: str = Field(..., description="预期结果")


class TestOutput(BaseModel):
    test_file: str = Field(..., description="测试文件路径")
    tests: List[TestCase] = Field(default_factory=list, description="测试用例列表")
    total_tests: int = Field(0, description="测试用例总数")


class GameplayResult(BaseModel):
    result_id: str = Field(..., description="结果ID")
    task_id: str = Field(..., description="任务ID")
    design_id: str = Field(..., description="设计文档ID")
    scene_output: Optional[SceneOutput] = Field(None, description="场景输出")
    script_output: Optional[ScriptOutput] = Field(None, description="脚本输出")
    test_output: Optional[TestOutput] = Field(None, description="测试输出")
    status: str = Field("completed", description="执行状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
