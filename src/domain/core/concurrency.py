from __future__ import annotations

from contextlib import contextmanager
from threading import BoundedSemaphore, Lock
from typing import Dict


_registry_guard = Lock()
_locks: Dict[str, Lock] = {}

_ia_guard = Lock()
_ia_semaphore: BoundedSemaphore = BoundedSemaphore(1)


def configure_ia_semaphore(max_in_flight: int) -> None:
    """Configure the semaphore used to throttle IA calls."""
    normalized = max(1, max_in_flight)
    with _ia_guard:
        global _ia_semaphore
        _ia_semaphore = BoundedSemaphore(normalized)


def get_lock(key: str) -> Lock:
    """Return a process-wide lock for the given key."""
    with _registry_guard:
        lock = _locks.get(key)
        if lock is None:
            lock = Lock()
            _locks[key] = lock
        return lock


def get_ia_semaphore() -> BoundedSemaphore:
    with _ia_guard:
        return _ia_semaphore


@contextmanager
def ia_slot():
    """Context manager that acquires/releases the IA semaphore."""
    semaphore = get_ia_semaphore()
    semaphore.acquire()
    try:
        yield
    finally:
        semaphore.release()
