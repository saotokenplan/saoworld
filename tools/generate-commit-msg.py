#!/usr/bin/env python3
"""
Git commit message helper: analyzes staged changes and suggests
a proper commit message based on actual diff content.

Helps ensure commit messages reflect actual changes rather than
session summaries or vague descriptions.

Usage:
    python tools/generate-commit-msg.py              # Output suggestion for staged changes
    python tools/generate-commit-msg.py --check-msg <msg-file>  # Check if message matches changes
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Optional


SCOPE_PATH_MAPPING = {
    # 文档相关 scope（与 .trae/rules/40-git-workflow.md 保持一致）
    "docs/00-governance": "docs",
    "docs/10-requirements": "requirements",
    "docs/20-specs": "specs",
    "docs/30-api": "api",
    "docs/40-dev-loop": "dev-loop",
    "docs/50-research": "docs",
    ".trae/skills": "skills",
    ".trae/rules": "rules",
    # 工程相关 scope（按模块命名）
    "services/vote": "vote",
    "services/gateway": "gateway",
    "services/player": "player",
    "services/world": "world",
    "services/generation": "generation",
    "services/review": "review",
    "services/content": "content",
    "services/ops": "ops",
    "game": "game",
    "workers": "workers",
    "infra": "infra",
    "tools": "tools",
    "telemetry": "telemetry",
}

TYPE_HINTS = {
    "docs": {".md", ".yaml", ".yml", ".txt", ".rst"},
    "test": {"tests/", "test_", "_test.", "conftest."},
    "chore": {"pyproject.toml", "requirements.txt", "Dockerfile", "docker-compose", ".gitignore", "Makefile"},
}

VAGUE_SUMMARIES = {
    "update",
    "updates",
    "updated",
    "wip",
    "fix stuff",
    "misc",
    "various",
    "temp",
    "tmp",
    "确定项目下一步行动",
    "优化错误响应 schema",
    "api 接口规范优化",
    "文档梳理与评估",
    "一些修改",
    "更新代码",
    "临时提交",
    "调试用",
    "修复bug",
    "bug fix",
    "minor changes",
    "small fixes",
}


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    return result.stdout


def get_staged_files() -> list[dict]:
    output = run_git(["diff", "--cached", "--name-status", "--diff-filter=ACMR"])
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


def get_staged_diff_stat() -> dict:
    output = run_git(["diff", "--cached", "--stat"])
    return {"raw": output}


def get_file_diff(path: str) -> str:
    return run_git(["diff", "--cached", "--", path])


def infer_scope(files: list[dict]) -> Optional[str]:
    if not files:
        return None

    scope_counts = Counter()
    for f in files:
        path = f["path"]
        matched = None
        for prefix, scope in SCOPE_PATH_MAPPING.items():
            if path.startswith(prefix + "/") or path == prefix:
                matched = scope
                break
        if matched:
            scope_counts[matched] += 1
        elif path.endswith(".md"):
            scope_counts["docs"] += 1
        elif path.startswith("."):
            scope_counts["tools"] += 1

    if not scope_counts:
        return None

    top_scope, count = scope_counts.most_common(1)[0]
    total = len(files)
    if count >= total * 0.5:
        return top_scope
    return None


def infer_type(files: list[dict], diff_stat: str) -> str:
    if not files:
        return "chore"

    paths = [f["path"] for f in files]
    all_test = all(
        any(hint in p for hint in TYPE_HINTS["test"]) for p in paths
    )
    if all_test and len(paths) > 0:
        has_non_test = any(
            not any(hint in p for hint in TYPE_HINTS["test"]) for p in paths
        )
        if not has_non_test:
            return "test"

    doc_count = sum(
        1 for p in paths
        if Path(p).suffix.lower() in TYPE_HINTS["docs"]
        or p.startswith("docs/")
    )
    if doc_count / len(paths) > 0.8:
        return "docs"

    chore_names = {n.lower() for n in TYPE_HINTS["chore"]}
    has_chore_only = all(
        Path(p).name.lower() in chore_names
        or any(p.endswith(ext) for ext in {".toml", ".txt", ".yml", ".yaml"})
        for p in paths
    )
    if has_chore_only and not any(p.startswith("services/") or p.startswith("game/") for p in paths):
        return "chore"

    added = 0
    deleted = 0
    for line in diff_stat.splitlines():
        m = re.search(r"(\d+) insertions?\(\+\)", line)
        if m:
            added += int(m.group(1))
        m = re.search(r"(\d+) deletions?\(-\)", line)
        if m:
            deleted += int(m.group(1))

    new_file_count = sum(1 for f in files if f["status"] == "A")
    if new_file_count > len(files) * 0.5 or added > deleted * 3:
        return "feat"

    return "feat"


def summarize_changes(files: list[dict], scope: Optional[str]) -> str:
    if not files:
        return "empty commit"

    by_dir = Counter()
    for f in files:
        parts = f["path"].split("/")
        if len(parts) >= 2:
            if parts[0] == "docs":
                key = "/".join(parts[:2])
            elif parts[0] == "services" and len(parts) >= 3:
                key = "/".join(parts[:3])
            else:
                key = parts[0]
        else:
            key = f["path"]
        by_dir[key] += 1

    status_map = {"A": "新增", "M": "修改", "C": "复制", "R": "重命名"}
    actions = []
    for f in files[:8]:
        action = status_map.get(f["status"], "修改")
        name = Path(f["path"]).name
        actions.append(f"{action}{name}")

    if scope == "vote":
        new_files = [f for f in files if f["status"] == "A"]
        if new_files and any("test" in f["path"] for f in new_files):
            return "新增投票服务测试用例"
        if any("routes" in f["path"] or "api" in f["path"] for f in files):
            return "新增投票接口实现"
        if any("schema" in f["path"] or "schemas" in f["path"] for f in files):
            return "补充投票数据结构定义"
        if any("model" in f["path"] or "domain" in f["path"] for f in files):
            return "调整投票领域模型"
        if any("repo" in f["path"] for f in files):
            return "补充投票数据仓储实现"

    if scope == "api":
        if any("example" in f["path"] for f in files):
            return "补充接口示例文档"
        if any("openapi" in f["path"] for f in files):
            return "更新 OpenAPI 规范"
        return "调整 API 文档"

    if scope == "specs":
        if any("engineering" in f["path"] for f in files):
            return "补充工程协作规范"
        if any("agent" in f["path"] for f in files):
            return "调整 Agent 闭环规范"
        if any("content" in f["path"] for f in files):
            return "补充内容生成规范"
        return "更新技术规范文档"

    if scope == "docs" or scope is None:
        if len(files) == 1:
            p = files[0]["path"]
            name = Path(p).stem
            if files[0]["status"] == "A":
                return f"新增{name}文档"
            return f"更新{name}文档"

    if scope in {"tools", "infra"}:
        if any("hook" in f["path"] for f in files):
            return "补充 Git hooks 配置"
        return "调整工具脚本"

    if scope == "game":
        return "更新游戏客户端代码"

    if scope == "skills":
        return "更新 Agent 技能配置"

    if len(files) <= 3:
        return f"{files[0]['path']} 等{len(files)}个文件改动"

    top_dirs = [d for d, _ in by_dir.most_common(2)]
    return f"更新 {'/'.join(top_dirs)} 相关内容"


def is_vague_summary(summary: str) -> bool:
    lower = summary.lower().strip()
    for vague in VAGUE_SUMMARIES:
        if lower == vague.lower() or lower.startswith(vague.lower()):
            return True
    if len(lower) < 6:
        return True
    return False


def generate_suggestion() -> dict:
    files = get_staged_files()
    if not files:
        return {
            "empty": True,
            "message": "",
            "hint": "没有检测到暂存的改动",
        }

    diff_stat = get_staged_diff_stat()["raw"]
    scope = infer_scope(files)
    commit_type = infer_type(files, diff_stat)
    summary = summarize_changes(files, scope)

    if scope:
        suggested = f"{commit_type}({scope}): {summary}"
    else:
        suggested = f"{commit_type}: {summary}"

    file_list = "\n".join(f"  - {f['status']} {f['path']}" for f in files[:15])
    if len(files) > 15:
        file_list += f"\n  ... 等共 {len(files)} 个文件"

    size_warnings = []
    added = 0
    deleted = 0
    for line in diff_stat.splitlines():
        m = re.search(r"(\d+) insertions?\(\+\)", line)
        if m:
            added += int(m.group(1))
        m = re.search(r"(\d+) deletions?\(-\)", line)
        if m:
            deleted += int(m.group(1))

    if len(files) >= 50:
        size_warnings.append(
            f"⚠️  文件数较多（{len(files)} 个），建议按模块/主题拆分为多次提交"
        )
    if added >= 2000:
        size_warnings.append(
            f"⚠️  新增行数较多（{added} 行），建议按功能点拆分为多次提交"
        )
    if added + deleted >= 3000:
        size_warnings.append(
            f"⚠️  总变更行数较多（{added + deleted} 行），建议拆分为更小的提交"
        )

    new_service_warnings = []
    new_services: set[str] = set()
    for f in files:
        if f["status"] == "A" and f["path"].startswith("services/"):
            parts = f["path"].split("/")
            if len(parts) >= 3 and parts[1]:
                new_services.add(parts[1])
    for service in new_services:
        has_app = any(
            f["status"] == "A" and f["path"].startswith(f"services/{service}/app/")
            for f in files
        )
        has_tests = any(
            f["status"] == "A" and f["path"].startswith(f"services/{service}/tests/")
            for f in files
        )
        if has_app and not has_tests:
            new_service_warnings.append(
                f"⚠️  新服务 '{service}' 新增了 app/ 代码但未包含 tests/ 测试文件，请补充基础测试"
            )

    warning_lines = []
    if size_warnings:
        warning_lines.extend(size_warnings)
    if new_service_warnings:
        warning_lines.extend(new_service_warnings)

    hint_parts = []
    hint_parts.append("# === 暂存改动分析 ===")
    hint_parts.append(f"# 检测到 {len(files)} 个文件待提交")
    hint_parts.append(f"# 新增 {added} 行，删除 {deleted} 行，总变更 {added + deleted} 行")
    hint_parts.append(f"# 推断 type: {commit_type}")
    hint_parts.append(f"# 推断 scope: {scope or '(未识别，请手动补充)'}")
    hint_parts.append(f"# 建议消息: {suggested}")
    hint_parts.append("#")
    if warning_lines:
        hint_parts.append("# === 提交提醒 ===")
        for w in warning_lines:
            hint_parts.append(f"# {w}")
        hint_parts.append("#")
    hint_parts.append("# 改动文件:")
    hint_parts.append(file_list)
    hint_parts.append("#")
    hint_parts.append("# 请根据实际改动编写准确的提交信息，而不是复制会话总结！")
    hint_parts.append("# 格式: <type>(<scope>): <summary>")
    hint_parts.append("# 示例: feat(vote): 增加投票提交接口")
    hint = "\n".join(hint_parts) + "\n"

    return {
        "empty": False,
        "message": suggested,
        "hint": hint,
        "type": commit_type,
        "scope": scope,
        "summary": summary,
        "files": files,
        "warnings": size_warnings + new_service_warnings,
        "added_lines": added,
        "deleted_lines": deleted,
    }


def check_message_matches_changes(message: str) -> list[str]:
    errors = []
    result = generate_suggestion()
    if result["empty"]:
        return errors

    title = message.splitlines()[0].strip() if message.splitlines() else ""
    pattern = re.compile(
        r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9_-]+)\))?:\s*(?P<summary>.+)$"
    )
    match = pattern.match(title)
    if not match:
        return errors

    summary = match.group("summary").strip()
    if is_vague_summary(summary):
        errors.append(
            f"提交摘要 '{summary}' 过于模糊或已被重复使用，"
            f"请基于实际改动编写具体描述。\n"
            f"建议参考: {result['message']}"
        )

    msg_scope = match.group("scope")
    inferred_scope = result["scope"]
    if msg_scope and inferred_scope and msg_scope != inferred_scope:
        errors.append(
            f"你指定的 scope 是 '{msg_scope}'，但根据改动文件推断应为 '{inferred_scope}'。\n"
            f"请确认 scope 是否准确反映实际改动模块。"
        )

    msg_type = match.group("type")
    files = result["files"]
    total = len(files)
    code_count = sum(
        1 for f in files
        if Path(f["path"]).suffix.lower() in {
            ".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs",
            ".c", ".cpp", ".java", ".rb", ".php", ".gd", ".swift", ".kt",
        }
    )
    code_ratio = code_count / total if total > 0 else 0

    if msg_type == "docs" and code_ratio > 0.3:
        errors.append(
            f"type 为 'docs' 但代码文件占比达 {code_ratio:.0%}（{code_count}/{total} 个文件），\n"
            f"提交 type 与实际变更性质严重不符。\n"
            f"若主要为代码变更，请使用 'feat'/'fix'/'refactor' 等 type。"
        )

    if "warnings" in result and result["warnings"]:
        errors.extend(result["warnings"])

    return errors


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--check-msg":
        msg_file = Path(sys.argv[2])
        if msg_file.exists():
            content = msg_file.read_text(encoding="utf-8")
            errors = check_message_matches_changes(content)
            if errors:
                print("=" * 60, file=sys.stderr)
                print("⚠️  提交信息可能未准确反映实际改动：", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                for i, err in enumerate(errors, 1):
                    print(f"  {i}. {err}", file=sys.stderr)
                print(file=sys.stderr)
                print("提交信息应基于本次实际改动生成，而不是会话总结。", file=sys.stderr)
                print("=" * 60, file=sys.stderr)
                return 1
        return 0

    result = generate_suggestion()
    if result["empty"]:
        print(result["hint"])
        return 0

    print(result["message"])
    print()
    print(result["hint"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
