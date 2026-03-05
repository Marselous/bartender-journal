from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.dependencies import get_optional_user
from app.helpers import resolve_author_name
from app.metrics import COMMENT_CREATE_SECONDS, COMMENTS_CREATED
from app.models import Comment, Post, User
from app.schemas import CommentCreateRequest, CommentResponse

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(post_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[CommentResponse]:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )
    comments = result.scalars().all()
    return [
        CommentResponse(
            id=c.id,
            post_id=c.post_id,
            created_at=c.created_at,
            body=c.body,
            author_name=c.author.username if c.author_id and c.author else c.author_name,
        )
        for c in comments
    ]


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: uuid.UUID,
    payload: CommentCreateRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    p = await db.execute(select(Post.id).where(Post.id == post_id))
    if not p.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    author_name = resolve_author_name(user, payload.author_name)
    comment = Comment(
        post_id=post_id,
        body=payload.body,
        author_id=user.id if user else None,
        author_name=None if user else author_name,
    )
    started = time.perf_counter()
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    COMMENTS_CREATED.inc()
    COMMENT_CREATE_SECONDS.observe(time.perf_counter() - started)
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        created_at=comment.created_at,
        body=comment.body,
        author_name=author_name,
    )
