#!/usr/bin/env python3
"""
Git commit message validator for open-world AI game project.

Validates that commit messages conform to the convention defined in
docs/20-specs/engineering-conventions.md:
    <type>(<scope>): <summary>

Usage:
    python tools/validate-commit-msg.py <commit-msg-file>
    python tools/validate-commit-msg.py --message "<message>"
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


VALID_TYPES = {"docs", "feat", "fix", "refactor", "test", "chore"}

VALID_SCOPES = {
    "docs",
    "specs",
    "requirements",
    "dev-loop",
    "skills",
    "api",
    "gateway",
    "player",
    "world",
    "vote",
    "generation",
    "review",
    "content",
    "ops",
    "game",
    "workers",
    "infra",
    "tools",
    "telemetry",
    "ui",
    "npc",
    "quest",
    "region",
    "event",
    "rules",
    "gates",
    "qa",
    "release",
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
            "提交标题过长（{} 字符），最大允许 {} 字符".format(len(title), MAX_SUMMARY_LENGTH)
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
            "无效的 type '{}'。允许的类型: {}".format(commit_type, ", ".join(sorted(VALID_TYPES)))
        )

    if scope is not None and scope not in VALID_SCOPES:
        errors.append(
            "scope '{}' 不在推荐列表中。推荐 scope: {}\n"
            "（若确实需要新 scope，请先更新 engineering-conventions.md 和本脚本）".format(
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
                "summary 不应以 '{}' 开头，请使用明确的动作动词（新增/补充/调整/修复/重构）".format(banned)
            )
            break

    for banned_phrase in BANNED_PHRASES:
        if banned_phrase in summary:
            errors.append("summary 包含模糊表述 '{}'，请更具体地描述改动内容".format(banned_phrase))

    if len(lines) > 1 and lines[1].strip() != "":
        errors.append("提交标题与正文之间需要保留一个空行")

    if len(lines) > 2:
        body_lines = [l for l in lines[2:] if l.strip() and not l.startswith("#")]
        for line in body_lines:
            if len(line) > 200:
                errors.append("正文中存在过长的行（{} 字符），建议每行不超过 200 字符".format(len(line)))
                break

    return errors


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

    if errors:
        print("=" * 60, file=sys.stderr)
        print("❌ 提交信息不符合规范！", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for i, err in enumerate(errors, 1):
            print("  {}. {}".format(i, err), file=sys.stderr)
        print(file=sys.stderr)
        print("参考文档: docs/20-specs/engineering-conventions.md#git-提交规范", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    print("✅ 提交信息符合规范")
    return 0


if __name__ == "__main__":
    sys.exit(main())
