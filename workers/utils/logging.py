import logging
import structlog

from workers.config import settings


def configure_logging() -> None:
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(message)s",
    )


def get_logger(task_name: str, trace_id: str | None = None) -> structlog.BoundLogger:
    logger = structlog.get_logger("workers")
    context = {"task_name": task_name}
    if trace_id:
        context["trace_id"] = trace_id
    return logger.bind(**context)