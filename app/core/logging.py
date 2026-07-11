"""Единая настройка структурированного логирования (structlog)."""
import logging
import sys

import structlog


def configure_logging(app_env: str = "production") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if app_env == "production" else logging.DEBUG,
    )
    structlog.configure(
        processors=[
            # Подмешивает contextvars (в частности request_id, см.
            # app/core/middleware.py:RequestIDMiddleware) в каждую запись лога
            # без необходимости явно прокидывать его через все сервисы.
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if app_env == "production" else structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    return structlog.get_logger(name)
