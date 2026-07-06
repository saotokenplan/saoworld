import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OpsErrorHandler:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def handle_error(self, error_type: str, message: str, context: Optional[dict] = None):
        handlers = {
            "collection_failure": self._handle_collection_failure,
            "data_inconsistency": self._handle_data_inconsistency,
            "alert_storm": self._handle_alert_storm,
            "analysis_failure": self._handle_analysis_failure,
            "report_failure": self._handle_report_failure,
            "workflow": self._handle_workflow_error,
        }
        handler = handlers.get(error_type, self._handle_generic_error)
        handler(message, context)

    def _handle_collection_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"数据采集失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 检查数据源连接，使用缓存数据或重试")

    def _handle_data_inconsistency(self, message: str, context: Optional[dict] = None):
        logger.warning(f"数据不一致: {message}")
        if context:
            logger.warning(f"上下文: {context}")
        logger.info("建议: 验证数据，优先信任更可靠的数据源")

    def _handle_alert_storm(self, message: str, context: Optional[dict] = None):
        logger.error(f"告警风暴: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 合并相似告警，抑制重复告警")

    def _handle_analysis_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"分析失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 使用简化分析或跳过该部分")

    def _handle_report_failure(self, message: str, context: Optional[dict] = None):
        logger.error(f"报告生成失败: {message}")
        if context:
            logger.error(f"上下文: {context}")
        logger.info("建议: 使用默认报告模板或生成简化报告")

    def _handle_workflow_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"运维工作流错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def _handle_generic_error(self, message: str, context: Optional[dict] = None):
        logger.error(f"运维错误: {message}")
        if context:
            logger.error(f"上下文: {context}")

    def log_ops_summary(self, ops_summary: dict):
        logger.info(f"运维摘要: {ops_summary}")
