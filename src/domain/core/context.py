from __future__ import annotations

from contextvars import ContextVar
from typing import Optional


_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def set_request_id(value: Optional[str]) -> None:
    _request_id.set(value)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_user_id(value: Optional[str]) -> None:
    _user_id.set(value)


def get_user_id() -> Optional[str]:
    return _user_id.get()


def clear_context() -> None:
    _request_id.set(None)
    _user_id.set(None)
