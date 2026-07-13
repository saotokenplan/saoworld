#!/usr/bin/env python3
"""
Git commit message validator for open-world AI game project.

Validates that commit messages conform to the convention defined in
.trae/rules/40-git-workflow.md:
    <type>(<scope>): <summary>

Additional checks:
- Commit size limits (files, lines)
- Type vs actual change consistency
- New service must include tests

Usage:
    python tools/validate-commit-msg.py <commit-msg-file>
    python tools/validate-commit-msg.py --message "<message>"
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


VALID_TYPES = {"docs", "feat", "fix", "refactor", "test", "chore"}

VALID_SCOPES = {
    # 文档相关 scope（与 .trae/rules/40-git-workflow.md 保持一致）
    "docs",
    "specs",
    "requirements",
    "dev-loop",
    "skills",
    "api",
    # 工程相关 scope（按模块命名）
    "gateway",
    "player",
    "world",
    "vote",
    "generation",
    "review",
    "content",
    "ops",
    "workers",
    "game",
    "infra",
    "telemetry",
    "tools",
    # .trae/rules/ 规则文件变更
    "rules",
}

COMMIT_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[a-z0-9_-]+)\))?"
    r": "
    r"(?P<summary>.+)$"
)

MAX_SUMMARY_LENGTH = 100

BANNED_PREFIXES = (
    "update",
    "updates",
    "updated",
    "wip",
    "fix stuff",
    "misc",
    "various",
    "temp",
    "tmp",
)

BANNED_PHRASES = (
    "修复bug",
    "一些修改",
    "更新代码",
    "临时提交",
    "调试用",
    "确定项目下一步行动",
    "优化错误响应",
    "接口规范优化",
    "文档梳理与评估",
    "bug fix",
    "minor changes",
    "small fixes",
)


def validate_commit_message(message):
    errors = []

    lines = message.splitlines()
    if not lines:
        return ["提交信息为空"]

    title = lines[0].strip()

    if not title:
        return ["提交标题为空"]

    if title.startswith("#"):
        return ["提交信息为注释，未实际提供提交标题"]

    if len(title) > MAX_SUMMARY_LENGTH:
        errors.append(
            "提交标题过长（{} 字符），最大允许 {} 字符".format(
                len(title), MAX_SUMMARY_LENGTH
            )
        )

    if title.endswith("."):
        errors.append("提交标题不应以句号结尾")

    match = COMMIT_PATTERN.match(title)
    if not match:
        errors.append(
            "提交标题格式不符合规范。\n"
            "正确格式: <type>(<scope>): <summary>\n"
            "示例: feat(vote): 增加投票提交接口\n"
            "你的标题: {}".format(title)
        )
        return errors

    commit_type = match.group("type")
    scope = match.group("scope")
    summary = match.group("summary").strip()

    if commit_type not in VALID_TYPES:
        errors.append(
            "无效的 type '{}'。允许的类型: {}".format(
                commit_type, ", ".join(sorted(VALID_TYPES))
            )
        )

    if scope is not None and scope not in VALID_SCOPES:
        errors.append(
            "scope '{}' 不在推荐列表中。推荐 scope: {}\n"
            "（若确实需要新 scope，请先更新 "
            "engineering-conventions.md 和本脚本）".format(
                scope, ", ".join(sorted(VALID_SCOPES))
            )
        )

    if not summary:
        errors.append("summary 为空，必须说明本次提交做了什么")
        return errors

    lower_summary = summary.lower()
    for banned in BANNED_PREFIXES:
        if lower_summary.startswith(banned):
            errors.append(
                "summary 不应以 '{}' 开头，"
                "请使用明确的动作动词（新增/补充/调整/修复/重构）".format(banned)
            )
            break

    for banned_phrase in BANNED_PHRASES:
        if banned_phrase in summary:
            errors.append(
                "summary 包含模糊表述 '{}'，"
                "请更具体地描述改动内容".format(banned_phrase)
            )

    if len(lines) > 1 and lines[1].strip() != "":
        errors.append("提交标题与正文之间需要保留一个空行")

    if len(lines) > 2:
        body_lines = [
            line for line in lines[2:]
            if line.strip() and not line.startswith("#")
        ]
        for line in body_lines:
            if len(line) > 200:
                errors.append(
                    "正文中存在过长的行（{} 字符），"
                    "建议每行不超过 200 字符".format(len(line))
                )
                break

    return errors


MAX_FILES_WARNING = 50
MAX_FILES_BLOCK = 100
MAX_INSERTIONS_WARNING = 2000
MAX_INSERTIONS_BLOCK = 5000
MAX_TOTAL_CHURN_WARNING = 3000
MAX_TOTAL_CHURN_BLOCK = 8000

CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".c", ".cpp",
    ".java", ".rb", ".php", ".gd", ".swift", ".kt",
}

DOC_EXTENSIONS = {".md", ".rst", ".txt"}

CONFIG_EXTENSIONS = {".yaml", ".yml", ".toml", ".json", ".ini", ".cfg"}


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    return result.stdout


def _get_staged_stat() -> dict | None:
    output = _run_git(["diff", "--cached", "--stat"])
    if not output.strip():
        return None
    lines = output.strip().splitlines()
    last_line = lines[-1].strip()
    files_changed = 0
    insertions = 0
    deletions = 0
    m = re.search(r"(\d+) files? changed", last_line)
    if m:
        files_changed = int(m.group(1))
    m = re.search(r"(\d+) insertions?\(\+\)", last_line)
    if m:
        insertions = int(m.group(1))
    m = re.search(r"(\d+) deletions?\(-\)", last_line)
    if m:
        deletions = int(m.group(1))
    return {
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "total_churn": insertions + deletions,
    }


def _get_staged_files() -> list[dict]:
    output = _run_git(["diff", "--cached", "--name-status", "--diff-filter=ACMR"])
    files = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        status = parts[0][0]
        path = parts[1]
        files.append({"status": status, "path": path})
    return files


def check_commit_size() -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    stat = _get_staged_stat()
    if stat is None:
        return warnings, errors

    files = stat["files_changed"]
    insertions = stat["insertions"]
    total_churn = stat["total_churn"]

    if files >= MAX_FILES_BLOCK:
        errors.append(
            "提交文件数过多（{} 个），超过上限 {} 个。\n"
            "请按模块/主题拆分为多次提交。\n"
            "（如确为初始化脚手架等特殊场景，可使用 --no-verify 绕过）".format(
                files, MAX_FILES_BLOCK
            )
        )
    elif files >= MAX_FILES_WARNING:
        warnings.append(
            "提交文件数较多（{} 个），建议拆分以提升审查质量。".format(files)
        )

    if insertions >= MAX_INSERTIONS_BLOCK:
        errors.append(
            "新增代码行数过多（{} 行），超过上限 {} 行。\n"
            "请按功能点拆分为多次提交。".format(insertions, MAX_INSERTIONS_BLOCK)
        )
    elif insertions >= MAX_INSERTIONS_WARNING:
        warnings.append(
            "新增代码行数较多（{} 行），建议拆分提交。".format(insertions)
        )

    if total_churn >= MAX_TOTAL_CHURN_BLOCK:
        errors.append(
            "总变更行数过多（{} 行），超过上限 {} 行。\n"
            "请拆分为更小的提交。".format(total_churn, MAX_TOTAL_CHURN_BLOCK)
        )
    elif total_churn >= MAX_TOTAL_CHURN_WARNING:
        warnings.append(
            "总变更行数较多（{} 行），建议拆分提交。".format(total_churn)
        )

    return warnings, errors


def check_type_consistency(commit_type: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    files = _get_staged_files()
    if not files:
        return warnings, errors

    code_count = 0
    doc_count = 0
    config_count = 0
    test_count = 0
    total = len(files)

    for f in files:
        path = f["path"]
        suffix = Path(path).suffix.lower()
        if "test" in path or "/tests/" in path or path.startswith("tests/"):
            test_count += 1
        if suffix in CODE_EXTENSIONS:
            code_count += 1
        elif suffix in DOC_EXTENSIONS:
            doc_count += 1
        elif suffix in CONFIG_EXTENSIONS:
            config_count += 1

    code_ratio = code_count / total if total > 0 else 0

    if commit_type == "docs" and code_ratio > 0.3:
        errors.append(
            "type 为 'docs' 但代码文件占比达 {:.0%}（{}/{} 个文件），\n"
            "提交 type 与实际变更性质不符。\n"
            "若主要为代码变更，请使用 'feat'/'fix'/'refactor' 等 type。".format(
                code_ratio, code_count, total
            )
        )
    elif commit_type == "docs" and code_ratio > 0.1:
        warnings.append(
            "type 为 'docs' 但代码文件占比达 {:.0%}，"
            "请注意 type 是否准确。".format(code_ratio)
        )

    if commit_type == "test" and code_ratio > 0.5 and test_count / total < 0.6:
        warnings.append(
            "type 为 'test' 但测试文件占比不高，请确认是否应使用其他 type。"
        )

    if commit_type == "chore" and code_ratio > 0.3:
        warnings.append(
            "type 为 'chore' 但包含较多代码文件（{:.0%}），"
            "请确认是否应使用 'feat' 或 'fix'。".format(
                code_ratio
            )
        )

    return warnings, errors


def check_new_service_has_tests() -> list[str]:
    warnings: list[str] = []

    files = _get_staged_files()
    if not files:
        return warnings

    new_services: set[str] = set()
    for f in files:
        if f["status"] != "A":
            continue
        path = f["path"]
        if path.startswith("services/"):
            parts = path.split("/")
            if len(parts) >= 3:
                service_name = parts[1]
                if service_name:
                    new_services.add(service_name)

    for service in new_services:
        has_app = any(
            f["status"] == "A"
            and f["path"].startswith(f"services/{service}/app/")
            for f in files
        )
        has_tests = any(
            f["status"] == "A"
            and f["path"].startswith(f"services/{service}/tests/")
            for f in files
        )
        if has_app and not has_tests:
            warnings.append(
                "新服务 '{}' 新增了 app/ 代码但未包含 tests/ 测试文件。\n"
                "按照测试规范，新服务必须附带基础测试（健康检查、核心接口、异常场景）。".format(
                    service
                )
            )

    return warnings


def main():
    if len(sys.argv) < 2:
        print("用法: python validate-commit-msg.py <commit-msg-file> [--allow-empty]")
        print("      python validate-commit-msg.py --message \"<message>\"")
        return 2

    allow_empty = "--allow-empty" in sys.argv

    if sys.argv[1] == "--message":
        if len(sys.argv) < 3:
            print("错误: --message 需要提供消息内容")
            return 2
        message = sys.argv[2]
    else:
        msg_file = Path(sys.argv[1])
        if not msg_file.exists():
            print("错误: 提交信息文件不存在: {}".format(msg_file))
            return 2
        message = msg_file.read_text(encoding="utf-8")

    clean_lines = []
    for line in message.splitlines():
        if not line.startswith("#"):
            clean_lines.append(line)
    cleaned = "\n".join(clean_lines).strip()

    if allow_empty and not cleaned:
        return 0

    errors = validate_commit_message(message)

    all_warnings: list[str] = []
    all_errors = list(errors)

    title = message.splitlines()[0].strip() if message.splitlines() else ""
    match = COMMIT_PATTERN.match(title)
    if match:
        commit_type = match.group("type")
        type_warnings, type_errors = check_type_consistency(commit_type)
        all_warnings.extend(type_warnings)
        all_errors.extend(type_errors)

    size_warnings, size_errors = check_commit_size()
    all_warnings.extend(size_warnings)
    all_errors.extend(size_errors)

    test_warnings = check_new_service_has_tests()
    all_warnings.extend(test_warnings)

    if all_errors:
        print("=" * 60, file=sys.stderr)
        print("❌ 提交不符合规范！", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        if all_errors:
            print("【错误】", file=sys.stderr)
            for i, err in enumerate(all_errors, 1):
                print("  {}. {}".format(i, err), file=sys.stderr)
        if all_warnings:
            print(file=sys.stderr)
            print("【警告】", file=sys.stderr)
            for i, warn in enumerate(all_warnings, 1):
                print("  {}. {}".format(i, warn), file=sys.stderr)
        print(file=sys.stderr)
        print("参考文档: .trae/rules/40-git-workflow.md", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    if all_warnings:
        print("⚠️  提交信息通过校验，但有以下提醒：")
        for i, warn in enumerate(all_warnings, 1):
            print("  {}. {}".format(i, warn))
        print()
        print("✅ 提交信息符合规范（有警告）")
        return 0

    print("✅ 提交信息符合规范")
    return 0


if __name__ == "__main__":
    sys.exit(main())
