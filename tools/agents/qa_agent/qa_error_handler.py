import logging
from typing import Optional

logger = logging.getLogger(__name__)


class QAErrorHandler:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def handle_error(self, error_type: str, message: str, context: Optional[dict] = None):
        handlers = {
            "environment": self._handle_environment_error,
            "missing_tests": self._handle_missing_tests_error,
            "flaky_tests": self._handle_flaky_tests_error,
            "timeout": self._handle_timeout_error,
            "fix_failure": self._handle_fix_failure_error,
            "workflow": self._handle_workflow_error,
        }
        handler = handlers.get(error_type, self._handle_generic_error)
        handler(message, context)

    def _handle_environment_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"测试环境错误: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 检查测试数据库配置或等待环境就绪")

    def _handle_missing_tests_error(self, message: str, context: Optional[dict] = None):
        logger.warning(f"测试用例缺失: {message}")
        if context:
            logger.warning(f"上下文: {context}")
        logger.info("建议: 为核心功能补充测试覆盖")

    def _handle_flaky_tests_error(self, message: str, context: Optional[dict] = None):
        logger.warning(f"测试不稳定: {message}")
        if context:
            logger.warning(f"上下文: {context}")
        logger.info("建议: 分析原因并修复不稳定的测试")

    def _handle_timeout_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"测试超时: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 优化测试或增加超时时间")

    def _handle_fix_failure_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"修复失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 升级为高优先级问题，通知人工介入")

    def _handle_workflow_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"QA 工作流错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def _handle_generic_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"QA 错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def log_failure_summary(self, failure_summary: dict):
        logger.error(f"失败摘要: {failure_summary}")
