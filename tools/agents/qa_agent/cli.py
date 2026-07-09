import argparse
import json
from .qa_agent import QAAgent
from .qa_input_schemas import TestTask, CodeChange


def main():
    parser = argparse.ArgumentParser(description="QA Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    generate_parser = subparsers.add_parser("generate-test", help="生成测试用例")
    generate_parser.add_argument("--task-id", required=True, help="测试任务ID")
    generate_parser.add_argument("--service", required=True, help="目标服务")
    generate_parser.add_argument("--type", required=True, help="测试类型")
    generate_parser.add_argument("--title", required=True, help="测试任务标题")
    generate_parser.add_argument("--requirement", action="append", required=True, help="测试需求")

    run_parser = subparsers.add_parser("run-tests", help="运行测试")
    run_parser.add_argument("--service", required=True, help="目标服务")

    analyze_parser = subparsers.add_parser("analyze-results", help="分析测试结果")
    analyze_parser.add_argument("--results", required=True, help="测试结果JSON文件")

    workflow_parser = subparsers.add_parser("run-workflow", help="运行完整QA工作流")
    workflow_parser.add_argument("--task-id", required=True, help="测试任务ID")
    workflow_parser.add_argument("--service", required=True, help="目标服务")
    workflow_parser.add_argument("--type", required=True, help="测试类型")
    workflow_parser.add_argument("--title", required=True, help="测试任务标题")
    workflow_parser.add_argument("--requirement", action="append", required=True, help="测试需求")

    args = parser.parse_args()
    agent = QAAgent()

    if args.command == "generate-test":
        code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
        test_task = TestTask(
            test_task_id=args.task_id,
            task_id="TASK-001",
            title=args.title,
            target_service=args.service,
            test_type=args.type,
            requirements=args.requirement,
            code_changes=code_changes
        )
        output = agent.write_test_cases(test_task)
        print(json.dumps(output.dict(), indent=2))

    elif args.command == "run-tests":
        results = agent.run_tests(args.service)
        print(json.dumps(results, indent=2))

    elif args.command == "analyze-results":
        with open(args.results, "r") as f:
            results = json.load(f)
        failures = agent.analyze_results(results)
        print(json.dumps([f.dict() for f in failures], indent=2))

    elif args.command == "run-workflow":
        code_changes = [CodeChange(path="app/api/routes.py", type="modified")]
        test_task = TestTask(
            test_task_id=args.task_id,
            task_id="TASK-001",
            title=args.title,
            target_service=args.service,
            test_type=args.type,
            requirements=args.requirement,
            code_changes=code_changes
        )
        result = agent.run_workflow(test_task)
        print(json.dumps(result.dict(), indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()