import logging
from typing import Optional

DEFAULT_LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Provide a configured logger instance scoped by name."""
    return logging.getLogger(name or "controladoria-api")
