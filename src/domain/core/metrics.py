from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Dict

_metrics: Counter = Counter()
_lock = Lock()


def increment(metric_name: str, value: int = 1) -> None:
    """Increase a counter metric."""
    with _lock:
        _metrics[metric_name] += value


def set_metric(metric_name: str, value: int) -> None:
    """Set a counter to a specific value (used sparingly for gauges)."""
    with _lock:
        _metrics[metric_name] = value


def snapshot() -> Dict[str, int]:
    """Return a copy of the current metrics."""
    with _lock:
        return dict(_metrics)
