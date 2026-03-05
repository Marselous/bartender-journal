"""Shared helper functions."""
from __future__ import annotations

from datetime import datetime, timezone

from app.constants import DEFAULT_AUTHOR_NAME
from app.models import User


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def resolve_author_name(user: User | None, provided_name: str | None = None) -> str:
    """Return the display name: username if authenticated, else provided_name or default."""
    if user:
        return user.username
    return provided_name or DEFAULT_AUTHOR_NAME
