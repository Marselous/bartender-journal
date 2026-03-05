"""Cursor-based pagination utilities."""
from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime

from fastapi import HTTPException


def encode_cursor(created_at: datetime, post_id: uuid.UUID) -> str:
    payload = {"created_at": created_at.isoformat(), "id": str(post_id)}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode((cursor + padding).encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        return datetime.fromisoformat(data["created_at"]), uuid.UUID(data["id"])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid cursor") from e
