from __future__ import annotations

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.domain.core.context import clear_context, set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request identifier to log context and response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            clear_context()
        response.headers["X-Request-ID"] = request_id
        return response
