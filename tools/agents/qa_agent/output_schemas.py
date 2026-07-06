from pydantic import BaseModel, Field
from typing import List, Optional


class TestCase(BaseModel):
    name: str = Field(description="测试用例名称")
    description: str = Field(description="测试用例描述")
    type: str = Field(description="测试类型：unit/integration/e2e")
    steps: List[dict] = Field(description="测试步骤")


class TestOutput(BaseModel):
    test_file: str = Field(description="测试文件路径")
    tests: List[TestCase] = Field(description="测试用例列表")


class ServiceTestResult(BaseModel):
    unit_tests: dict = Field(description="单元测试结果")
    integration_tests: dict = Field(description="集成测试结果")
    lint: dict = Field(description="静态检查结果")
    typecheck: dict = Field(description="类型检查结果")


class TestReportSummary(BaseModel):
    overall_status: str = Field(description="总体状态：pass/fail")
    total_passed: int = Field(description="通过测试总数")
    total_failed: int = Field(description="失败测试总数")
    total_tests: int = Field(description="测试总数")


class TestReport(BaseModel):
    report_id: str = Field(description="报告ID")
    test_task_id: str = Field(description="测试任务ID")
    timestamp: str = Field(description="生成时间")
    results: dict = Field(description="各服务测试结果")
    summary: TestReportSummary = Field(description="测试摘要")


class FailureSummary(BaseModel):
    failure_id: str = Field(description="失败ID")
    test_name: str = Field(description="测试名称")
    service: str = Field(description="服务名称")
    error_type: str = Field(description="错误类型")
    error_message: str = Field(description="错误消息")
    stack_trace: Optional[str] = Field(default=None, description="堆栈跟踪")
    suggestion: str = Field(description="修复建议")
    related_tests: List[str] = Field(description="相关测试")
    priority: str = Field(description="优先级：high/medium/low")


class QAResult(BaseModel):
    success: bool = Field(description="是否成功")
    report: Optional[TestReport] = Field(default=None, description="测试报告")
    failures: List[FailureSummary] = Field(description="失败摘要列表")
    message: str = Field(description="结果消息")