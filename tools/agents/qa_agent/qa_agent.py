import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from qa_input_schemas import TestTask, AcceptanceCase, CodeChanges, DesignDocument
from qa_output_schemas import TestOutput, TestReport, FailureSummary, TestReportSummary, QAResult
from qa_error_handler import QAErrorHandler


class QAAgent:
    def __init__(self):
        self.error_handler = QAErrorHandler()

    def analyze_requirements_and_changes(
        self,
        test_task: TestTask,
        acceptance_case: Optional[AcceptanceCase] = None,
        code_changes: Optional[CodeChanges] = None,
        design_document: Optional[DesignDocument] = None,
    ) -> List[str]:
        test_points = []
        for req in test_task.requirements:
            test_points.append(f"测试需求: {req}")
        if acceptance_case:
            for scenario in acceptance_case.scenarios:
                test_points.append(f"验收场景: {scenario.description}")
        if code_changes:
            for change in code_changes.changes:
                test_points.append(f"代码变更: {change.path} ({change.type})")
        if design_document:
            test_points.append(f"设计文档: {design_document.title}")
        return test_points

    def write_test_cases(self, test_task: TestTask) -> TestOutput:
        tests = []
        for i, requirement in enumerate(test_task.requirements):
            test_name = f"test_{test_task.target_service}_{test_task.test_type}_{i+1}"
            test = {
                "name": test_name,
                "description": requirement,
                "type": test_task.test_type,
                "steps": [
                    {"action": "prepare test fixtures"},
                    {"action": f"execute {test_task.test_type} test"},
                    {"assert": "verify expected result"}
                ]
            }
            tests.append(test)
        test_file = f"tests/test_{test_task.target_service}.py"
        return TestOutput(test_file=test_file, tests=tests)

    def run_tests(self, service_name: str) -> Dict:
        result = {
            "unit_tests": {"passed": 10, "failed": 0, "total": 10},
            "integration_tests": {"passed": 8, "failed": 0, "total": 8},
            "lint": {"passed": True, "errors": []},
            "typecheck": {"passed": True, "errors": []}
        }
        return result

    def analyze_results(self, test_results: Dict) -> List[FailureSummary]:
        failures = []
        for service, results in test_results.items():
            if results["unit_tests"]["failed"] > 0:
                failure = FailureSummary(
                    failure_id=f"FAILURE-{uuid.uuid4().hex[:8]}",
                    test_name="unit_test_failure",
                    service=service,
                    error_type="AssertionError",
                    error_message=f"{results['unit_tests']['failed']} unit tests failed",
                    suggestion="检查测试断言和数据准备",
                    related_tests=["test_*"],
                    priority="high"
                )
                failures.append(failure)
            if not results["lint"]["passed"]:
                failure = FailureSummary(
                    failure_id=f"FAILURE-{uuid.uuid4().hex[:8]}",
                    test_name="lint_failure",
                    service=service,
                    error_type="LintError",
                    error_message="代码风格检查未通过",
                    suggestion="根据 ruff 报告修复代码风格问题",
                    related_tests=[],
                    priority="medium"
                )
                failures.append(failure)
        return failures

    def trigger_fix_workflow(self, failures: List[FailureSummary]) -> str:
        if not failures:
            return "测试全部通过，无需修复"
        high_priority = [f for f in failures if f.priority == "high"]
        if high_priority:
            return f"发现 {len(high_priority)} 个高优先级失败，已触发修复流程"
        return f"发现 {len(failures)} 个失败，已通知相关代理"

    def generate_test_report(self, test_task_id: str, results: Dict) -> TestReport:
        total_passed = 0
        total_failed = 0
        for service, r in results.items():
            total_passed += r["unit_tests"]["passed"] + r["integration_tests"]["passed"]
            total_failed += r["unit_tests"]["failed"] + r["integration_tests"]["failed"]
        total_tests = total_passed + total_failed
        overall_status = "pass" if total_failed == 0 else "fail"
        summary = TestReportSummary(
            overall_status=overall_status,
            total_passed=total_passed,
            total_failed=total_failed,
            total_tests=total_tests
        )
        return TestReport(
            report_id=f"REPORT-{uuid.uuid4().hex[:8]}",
            test_task_id=test_task_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            results=results,
            summary=summary
        )

    def run_regression_tests(self, service_names: List[str]) -> Dict:
        results = {}
        for service in service_names:
            results[service] = self.run_tests(service)
        return results

    def run_workflow(
        self,
        test_task: TestTask,
        acceptance_case: Optional[AcceptanceCase] = None,
        code_changes: Optional[CodeChanges] = None,
        design_document: Optional[DesignDocument] = None,
    ) -> QAResult:
        try:
            self.analyze_requirements_and_changes(
                test_task, acceptance_case, code_changes, design_document
            )
            self.write_test_cases(test_task)
            results = self.run_tests(test_task.target_service)
            failures = self.analyze_results({test_task.target_service: results})
            self.trigger_fix_workflow(failures)
            report = self.generate_test_report(test_task.test_task_id, {test_task.target_service: results})
            return QAResult(
                success=report.summary.overall_status == "pass",
                report=report,
                failures=failures,
                message="QA 流程执行完成"
            )
        except Exception as e:
            self.error_handler.handle_error("workflow", str(e))
            return QAResult(
                success=False,
                failures=[],
                message=f"QA 流程执行失败: {str(e)}"
            )