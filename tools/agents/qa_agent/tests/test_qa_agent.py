import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from qa_agent import QAAgent
from input_schemas import TestTask, AcceptanceCase, CodeChange, AcceptanceScenario, ScenarioStep


def test_analyze_requirements_and_changes():
    agent = QAAgent()
    code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
    test_task = TestTask(
        test_task_id="TEST-001",
        task_id="TASK-001",
        title="区域创建接口测试",
        target_service="world-service",
        test_type="integration",
        requirements=["测试区域创建成功", "测试区域名称重复"],
        code_changes=code_changes
    )
    test_points = agent.analyze_requirements_and_changes(test_task)
    assert len(test_points) == 2
    assert "测试需求: 测试区域创建成功" in test_points
    assert "测试需求: 测试区域名称重复" in test_points


def test_analyze_with_acceptance_case():
    agent = QAAgent()
    code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
    test_task = TestTask(
        test_task_id="TEST-001",
        task_id="TASK-001",
        title="区域创建接口测试",
        target_service="world-service",
        test_type="integration",
        requirements=["测试区域创建成功"],
        code_changes=code_changes
    )
    scenario = AcceptanceScenario(
        id="SCENARIO-001",
        description="管理员创建区域",
        steps=[ScenarioStep(action="POST /api/v1/world/regions")]
    )
    acceptance_case = AcceptanceCase(
        acceptance_id="ACC-001",
        task_id="TASK-001",
        title="区域创建验收",
        scenarios=[scenario]
    )
    test_points = agent.analyze_requirements_and_changes(test_task, acceptance_case=acceptance_case)
    assert len(test_points) == 2
    assert "验收场景: 管理员创建区域" in test_points


def test_write_test_cases():
    agent = QAAgent()
    code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
    test_task = TestTask(
        test_task_id="TEST-001",
        task_id="TASK-001",
        title="区域创建接口测试",
        target_service="world-service",
        test_type="integration",
        requirements=["测试区域创建成功", "测试区域名称重复"],
        code_changes=code_changes
    )
    output = agent.write_test_cases(test_task)
    assert output.test_file == "tests/test_world-service.py"
    assert len(output.tests) == 2
    assert output.tests[0].name == "test_world-service_integration_1"
    assert output.tests[0].description == "测试区域创建成功"


def test_run_tests():
    agent = QAAgent()
    results = agent.run_tests("world-service")
    assert "unit_tests" in results
    assert "integration_tests" in results
    assert "lint" in results
    assert "typecheck" in results
    assert results["unit_tests"]["passed"] == 10
    assert results["unit_tests"]["failed"] == 0


def test_analyze_results_no_failures():
    agent = QAAgent()
    results = {
        "world-service": {
            "unit_tests": {"passed": 10, "failed": 0, "total": 10},
            "integration_tests": {"passed": 8, "failed": 0, "total": 8},
            "lint": {"passed": True, "errors": []},
            "typecheck": {"passed": True, "errors": []}
        }
    }
    failures = agent.analyze_results(results)
    assert len(failures) == 0


def test_analyze_results_with_failures():
    agent = QAAgent()
    results = {
        "world-service": {
            "unit_tests": {"passed": 8, "failed": 2, "total": 10},
            "integration_tests": {"passed": 8, "failed": 0, "total": 8},
            "lint": {"passed": True, "errors": []},
            "typecheck": {"passed": True, "errors": []}
        }
    }
    failures = agent.analyze_results(results)
    assert len(failures) == 1
    assert failures[0].priority == "high"
    assert "2 unit tests failed" in failures[0].error_message


def test_trigger_fix_workflow_no_failures():
    agent = QAAgent()
    result = agent.trigger_fix_workflow([])
    assert "测试全部通过，无需修复" in result


def test_trigger_fix_workflow_with_failures():
    agent = QAAgent()
    failures = [
        type('obj', (object,), {'priority': 'high'})(),
        type('obj', (object,), {'priority': 'medium'})()
    ]
    result = agent.trigger_fix_workflow(failures)
    assert "1 个高优先级失败" in result


def test_generate_test_report():
    agent = QAAgent()
    results = {
        "world-service": {
            "unit_tests": {"passed": 10, "failed": 0, "total": 10},
            "integration_tests": {"passed": 8, "failed": 0, "total": 8},
            "lint": {"passed": True, "errors": []},
            "typecheck": {"passed": True, "errors": []}
        }
    }
    report = agent.generate_test_report("TEST-001", results)
    assert report.report_id.startswith("REPORT-")
    assert report.test_task_id == "TEST-001"
    assert report.summary.overall_status == "pass"
    assert report.summary.total_passed == 18
    assert report.summary.total_failed == 0


def test_run_regression_tests():
    agent = QAAgent()
    results = agent.run_regression_tests(["vote-service", "world-service"])
    assert len(results) == 2
    assert "vote-service" in results
    assert "world-service" in results


def test_run_workflow_success():
    agent = QAAgent()
    code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
    test_task = TestTask(
        test_task_id="TEST-001",
        task_id="TASK-001",
        title="区域创建接口测试",
        target_service="world-service",
        test_type="integration",
        requirements=["测试区域创建成功"],
        code_changes=code_changes
    )
    result = agent.run_workflow(test_task)
    assert result.success is True
    assert result.report is not None
    assert result.report.summary.overall_status == "pass"
    assert len(result.failures) == 0


def test_error_handler_handle_environment_error():
    from tools.agents.qa_agent.error_handler import QAErrorHandler
    handler = QAErrorHandler()
    handler.handle_error("environment", "数据库连接失败")


def test_error_handler_handle_missing_tests_error():
    from tools.agents.qa_agent.error_handler import QAErrorHandler
    handler = QAErrorHandler()
    handler.handle_error("missing_tests", "核心功能缺少测试覆盖")


def test_error_handler_handle_flaky_tests_error():
    from tools.agents.qa_agent.error_handler import QAErrorHandler
    handler = QAErrorHandler()
    handler.handle_error("flaky_tests", "测试结果不一致")


def test_error_handler_handle_timeout_error():
    from tools.agents.qa_agent.error_handler import QAErrorHandler
    handler = QAErrorHandler()
    handler.handle_error("timeout", "测试执行超时")


def test_error_handler_handle_fix_failure_error():
    from tools.agents.qa_agent.error_handler import QAErrorHandler
    handler = QAErrorHandler()
    handler.handle_error("fix_failure", "修复多次仍未通过")