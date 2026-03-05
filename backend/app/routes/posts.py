from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cache import cache_get_json, cache_set_json
from app.constants import FEED_CACHE_KEY_TEMPLATE, FEED_CACHE_TTL_SECONDS
from app.db import get_db
from app.dependencies import get_optional_user
from app.helpers import resolve_author_name
from app.metrics import FEED_CACHE_REQUESTS, POST_CREATE_SECONDS, POSTS_CREATED
from app.models import Comment, Post, PostType, User
from app.pagination import decode_cursor, encode_cursor
from app.schemas import CursorPage, PostCreateRequest, PostResponse

router = APIRouter(tags=["posts"])


@router.get("/posts", response_model=CursorPage)
async def list_posts(
    limit: int = 10,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> CursorPage:
    limit = max(1, min(limit, 50))

    cache_key = FEED_CACHE_KEY_TEMPLATE.format(limit=limit, cursor=cursor or "")
    cached = await cache_get_json(cache_key)
    if cached is not None:
        FEED_CACHE_REQUESTS.labels(outcome="hit").inc()
        return CursorPage(**cached)

    FEED_CACHE_REQUESTS.labels(outcome="miss").inc()

    q = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(desc(Post.created_at), desc(Post.id))
        .limit(limit + 1)
    )
    if cursor:
        (created_at, post_id) = decode_cursor(cursor)
        q = q.where(
            (Post.created_at < created_at)
            | ((Post.created_at == created_at) & (Post.id < post_id))
        )

    result = await db.execute(q)
    posts = list(result.scalars().all())

    has_more = len(posts) > limit
    posts = posts[:limit]

    counts: dict[uuid.UUID, int] = {}
    if posts:
        post_ids = [p.id for p in posts]
        c_result = await db.execute(
            select(Comment.post_id, func.count(Comment.id))
            .where(Comment.post_id.in_(post_ids))
            .group_by(Comment.post_id)
        )
        counts = {row[0]: int(row[1]) for row in c_result.all()}

    items = [
        PostResponse(
            id=p.id,
            created_at=p.created_at,
            type=PostType(p.type),
            title=p.title,
            body=p.body,
            link_url=p.link_url,
            image_url=p.image_url,
            author_name=p.author.username if p.author_id and p.author else p.author_name,
            comment_count=counts.get(p.id, 0),
        )
        for p in posts
    ]

    next_cursor = encode_cursor(posts[-1].created_at, posts[-1].id) if has_more and posts else None
    page = CursorPage(items=items, next_cursor=next_cursor)
    await cache_set_json(cache_key, page.model_dump(mode="json"), ttl_seconds=FEED_CACHE_TTL_SECONDS)
    return page


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    payload: PostCreateRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    if payload.type == PostType.text and not payload.body:
        raise HTTPException(status_code=400, detail="body is required for text posts")
    if payload.type == PostType.link and not payload.link_url:
        raise HTTPException(status_code=400, detail="link_url is required for link posts")
    if payload.type == PostType.photo and not payload.image_url:
        raise HTTPException(status_code=400, detail="image_url is required for photo posts")

    author_name = resolve_author_name(user, payload.author_name)

    post = Post(
        type=payload.type,
        title=payload.title,
        body=payload.body,
        link_url=str(payload.link_url) if payload.link_url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        author_id=user.id if user else None,
        author_name=None if user else author_name,
    )
    started = time.perf_counter()
    db.add(post)
    await db.commit()
    await db.refresh(post)
    post_type_value = post.type.value if isinstance(post.type, PostType) else str(post.type)
    POSTS_CREATED.labels(type=post_type_value).inc()
    POST_CREATE_SECONDS.observe(time.perf_counter() - started)

    return PostResponse(
        id=post.id,
        created_at=post.created_at,
        type=PostType(post.type),
        title=post.title,
        body=post.body,
        link_url=post.link_url,
        image_url=post.image_url,
        author_name=author_name,
        comment_count=0,
    )
