from __future__ import annotations

from fastapi import APIRouter

from app.helpers import now_utc

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "ts": now_utc().isoformat()}
