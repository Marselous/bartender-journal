"""Custom ASGI middleware."""
from __future__ import annotations

from fastapi import Request

from app.constants import APP_HEADER_NAME, APP_HEADER_VALUE


async def add_app_header(request: Request, call_next):
    response = await call_next(request)
    response.headers[APP_HEADER_NAME] = APP_HEADER_VALUE
    return response
