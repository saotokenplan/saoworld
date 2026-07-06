import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BuildErrorHandler:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def handle_error(self, error_type: str, message: str, context: Optional[dict] = None):
        handlers = {
            "build_failure": self._handle_build_failure,
            "image_push_failure": self._handle_image_push_failure,
            "missing_content": self._handle_missing_content,
            "rollback_failure": self._handle_rollback_failure,
            "resource_insufficient": self._handle_resource_insufficient,
            "workflow": self._handle_workflow_error,
        }
        handler = handlers.get(error_type, self._handle_generic_error)
        handler(message, context)

    def _handle_build_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"构建失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 分析错误日志，修复问题后重新构建")

    def _handle_image_push_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"镜像推送失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 检查网络连接和仓库权限，重新推送")

    def _handle_missing_content(self, message: str, context: Optional[dict] = None):
        logger.warning(f"内容包缺失: {message}")
        if context:
            logger.warning(f"上下文: {context}")
        logger.info("建议: 等待内容包生成或使用空内容包")

    def _handle_rollback_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"回滚包生成失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 重新生成回滚包，确保包含所有必要文件")

    def _handle_resource_insufficient(self, message: str, context: Optional[dict] = None):
        logger.error(f"资源不足: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 清理临时文件，增加资源分配")

    def _handle_workflow_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"构建工作流错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def _handle_generic_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"构建错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def log_build_summary(self, build_summary: dict):
        logger.info(f"构建摘要: {build_summary}")
