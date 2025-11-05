import logging
from typing import Optional

from src.domain.core.context import get_request_id, get_user_id

DEFAULT_LOG_LEVEL = logging.INFO


class ContextFormatter(logging.Formatter):
    """Formatter that guarantees request/user identifiers are present."""

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id() or "-"
        if not hasattr(record, "user_id"):
            record.user_id = get_user_id() or "-"
        return super().format(record)


logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format="%(asctime)s %(name)s %(levelname)s request_id=%(request_id)s user_id=%(user_id)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

formatter = ContextFormatter(
    "%(asctime)s %(name)s %(levelname)s request_id=%(request_id)s user_id=%(user_id)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

for handler in logging.getLogger().handlers:
    handler.setFormatter(formatter)


_previous_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _previous_factory(*args, **kwargs)
    if not hasattr(record, "request_id"):
        record.request_id = get_request_id() or "-"
    if not hasattr(record, "user_id"):
        record.user_id = get_user_id() or "-"
    return record


logging.setLogRecordFactory(_record_factory)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Provide a configured logger instance scoped by name."""
    return logging.getLogger(name or "controladoria-api")
