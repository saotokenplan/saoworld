"""
Backend Agent 错误处理模块

处理设计不完整、模型冲突、SQLAlchemy 错误、测试失败、类型检查失败等异常情况。
"""

import uuid
from datetime import datetime
from typing import Any


class BackendErrorHandler:
    """Backend Agent 错误处理器"""

    def __init__(self) -> None:
        """初始化错误处理器"""
        self.error_log: list[dict[str, Any]] = []

    def handle_design_incomplete(
        self, message: str, context: dict[str, Any]
    ) -> str:
        """处理设计不完整错误

        Args:
            message: 错误消息
            context: 错误上下文

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "design_incomplete",
            "message": message,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "action": "向 System Designer Agent 请求补充设计",
        }
        self.error_log.append(error_record)

        error_str = f"[{error_id}] 设计不完整：{message}"
        return error_str

    def handle_model_conflict(
        self, message: str, existing_model: str, new_model: str
    ) -> str:
        """处理模型冲突

        Args:
            message: 错误消息
            existing_model: 已有模型名
            new_model: 新模型名

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "model_conflict",
            "message": message,
            "existing_model": existing_model,
            "new_model": new_model,
            "timestamp": datetime.now().isoformat(),
            "action": "分析冲突原因，调整模型命名或迁移策略",
        }
        self.error_log.append(error_record)

        error_str = (
            f"[{error_id}] 模型冲突：{message} "
            f"(已有模型: {existing_model}, 新模型: {new_model})"
        )
        return error_str

    def handle_sqlalchemy_error(
        self, message: str, code_snippet: str, error_detail: str
    ) -> str:
        """处理 SQLAlchemy 错误

        Args:
            message: 错误消息
            code_snippet: 错误代码片段
            error_detail: 详细错误信息

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "sqlalchemy_error",
            "message": message,
            "code_snippet": code_snippet,
            "error_detail": error_detail,
            "timestamp": datetime.now().isoformat(),
            "action": "修复 SQLAlchemy 模型定义或查询语句",
        }
        self.error_log.append(error_record)

        error_str = f"[{error_id}] SQLAlchemy 错误：{message}\n代码：{code_snippet}\n详情：{error_detail}"
        return error_str

    def handle_test_failure(
        self, message: str, failed_tests: list[str], test_output: str
    ) -> str:
        """处理测试失败

        Args:
            message: 错误消息
            failed_tests: 失败测试名称列表
            test_output: 测试输出内容

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "test_failure",
            "message": message,
            "failed_tests": failed_tests,
            "test_output": test_output,
            "timestamp": datetime.now().isoformat(),
            "action": "分析失败原因，修复代码逻辑",
        }
        self.error_log.append(error_record)

        error_str = (
            f"[{error_id}] 测试失败：{message}\n"
            f"失败测试：{', '.join(failed_tests)}\n"
            f"输出：{test_output[:200]}..."
        )
        return error_str

    def handle_type_check_failure(
        self, message: str, type_errors: list[str]
    ) -> str:
        """处理类型检查失败

        Args:
            message: 错误消息
            type_errors: 类型错误列表

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "type_check_failure",
            "message": message,
            "type_errors": type_errors,
            "timestamp": datetime.now().isoformat(),
            "action": "修复类型注解或代码逻辑",
        }
        self.error_log.append(error_record)

        error_str = (
            f"[{error_id}] 类型检查失败：{message}\n"
            f"类型错误：{len(type_errors)} 个\n"
            f"示例：{type_errors[0] if type_errors else '无'}"
        )
        return error_str

    def handle_api_conflict(
        self, message: str, existing_endpoint: str, new_endpoint: str
    ) -> str:
        """处理 API 冲突

        Args:
            message: 错误消息
            existing_endpoint: 已有端点
            new_endpoint: 新端点

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "api_conflict",
            "message": message,
            "existing_endpoint": existing_endpoint,
            "new_endpoint": new_endpoint,
            "timestamp": datetime.now().isoformat(),
            "action": "调整端点路径或合并功能",
        }
        self.error_log.append(error_record)

        error_str = (
            f"[{error_id}] API 冲突：{message} "
            f"(已有端点: {existing_endpoint}, 新端点: {new_endpoint})"
        )
        return error_str

    def handle_migration_error(
        self, message: str, migration_file: str, error_detail: str
    ) -> str:
        """处理迁移脚本错误

        Args:
            message: 错误消息
            migration_file: 迁移文件路径
            error_detail: 详细错误信息

        Returns:
            错误字符串
        """
        error_id = f"ERROR-{uuid.uuid4().hex[:8]}"
        error_record = {
            "error_id": error_id,
            "error_type": "migration_error",
            "message": message,
            "migration_file": migration_file,
            "error_detail": error_detail,
            "timestamp": datetime.now().isoformat(),
            "action": "检查迁移脚本逻辑，修复 SQL 语句",
        }
        self.error_log.append(error_record)

        error_str = (
            f"[{error_id}] 迁移脚本错误：{message}\n"
            f"文件：{migration_file}\n"
            f"详情：{error_detail}"
        )
        return error_str

    def get_error_summary(self) -> dict[str, Any]:
        """获取错误摘要

        Returns:
            错误摘要统计
        """
        error_types = {}
        for error in self.error_log:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "error_types": error_types,
            "last_error": self.error_log[-1] if self.error_log else None,
        }

    def clear_errors(self) -> None:
        """清空错误日志"""
        self.error_log = []

    def log_warning(self, message: str, context: dict[str, Any]) -> str:
        """记录警告信息

        Args:
            message: 警告消息
            context: 警告上下文

        Returns:
            警告字符串
        """
        warning_id = f"WARN-{uuid.uuid4().hex[:8]}"
        warning_record = {
            "warning_id": warning_id,
            "message": message,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        }
        self.error_log.append(warning_record)

        warning_str = f"[{warning_id}] 警告：{message}"
        return warning_str