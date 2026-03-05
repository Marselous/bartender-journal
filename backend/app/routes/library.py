from __future__ import annotations

from typing import TypeVar

from fastapi import APIRouter
from pydantic import BaseModel

from app.cache import cache_get_json, cache_set_json
from app.constants import (
    LIBRARY_CACHE_TTL_SECONDS,
    LIBRARY_HISTORY_CACHE_KEY,
    LIBRARY_PLACES_CACHE_KEY,
    LIBRARY_RECIPES_CACHE_KEY,
)
from app.schemas import HistoryEntry, Place, Recipe

router = APIRouter(prefix="/library", tags=["library"])

T = TypeVar("T", bound=BaseModel)


async def _cached_seed_data(cache_key: str, model_cls: type[T], seed: list[T]) -> list[T]:
    """Return cached data or seed it."""
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return [model_cls(**item) for item in cached]
    await cache_set_json(
        cache_key,
        [item.model_dump(mode="json") for item in seed],
        ttl_seconds=LIBRARY_CACHE_TTL_SECONDS,
    )
    return seed


@router.get("/recipes", response_model=list[Recipe])
async def recipes() -> list[Recipe]:
    return await _cached_seed_data(LIBRARY_RECIPES_CACHE_KEY, Recipe, [
        Recipe(id="old-fashioned", title="Old Fashioned", tags=["classic", "whiskey"]),
        Recipe(id="negroni", title="Negroni", tags=["classic", "gin"]),
        Recipe(id="daiquiri", title="Daiquiri", tags=["rum", "sour"]),
    ])


@router.get("/places", response_model=list[Place])
async def places() -> list[Place]:
    return await _cached_seed_data(LIBRARY_PLACES_CACHE_KEY, Place, [
        Place(id="favorite-local", name="Your Favorite Local", city="(add city)"),
        Place(id="hotel-bar", name="A Great Hotel Bar", city="(add city)"),
    ])


@router.get("/history", response_model=list[HistoryEntry])
async def history() -> list[HistoryEntry]:
    return await _cached_seed_data(LIBRARY_HISTORY_CACHE_KEY, HistoryEntry, [
        HistoryEntry(id="ice", title="Why ice quality matters"),
        HistoryEntry(id="bitters", title="Bitters: the bartender's spice rack"),
    ])
