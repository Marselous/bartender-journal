from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqladmin import Admin, ModelView

from app.db import engine, get_db
from app.cache import cache_get_json, cache_set_json
from app.models import Comment, Post, PostType, User
from app.schemas import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthTokenResponse,
    CommentCreateRequest,
    CommentResponse,
    CursorPage,
    HistoryEntry,
    Place,
    PostCreateRequest,
    PostResponse,
    Recipe,
)
from app.security import create_access_token, decode_token, hash_password, verify_password
from app.settings import settings

app = FastAPI(title=settings.app_name)

resource = Resource.create({"service.name": "bartender-journal-api"})
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.username, User.created_at]
    column_searchable_list = [User.email, User.username]
    column_sortable_list = [User.created_at]


class PostAdmin(ModelView, model=Post):
    column_list = [Post.id, Post.created_at, Post.type, Post.title, Post.author_id]
    column_searchable_list = [Post.title, Post.body]
    column_sortable_list = [Post.created_at]


class CommentAdmin(ModelView, model=Comment):
    column_list = [Comment.id, Comment.post_id, Comment.created_at, Comment.author_id]
    column_searchable_list = [Comment.body]
    column_sortable_list = [Comment.created_at]


admin = Admin(app, engine)
admin.add_view(UserAdmin)
admin.add_view(PostAdmin)
admin.add_view(CommentAdmin)

instrumentator = Instrumentator()


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


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


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()
    except Exception:  # noqa: BLE001
        return None


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "ts": _now_utc().isoformat()}


@app.on_event("startup")
async def _startup_instrumentation() -> None:
    # Prometheus metrics at /metrics
    instrumentator.instrument(app).expose(app)


@app.post("/auth/register", response_model=AuthTokenResponse, status_code=201)
async def register(payload: AuthRegisterRequest, db: AsyncSession = Depends(get_db)) -> AuthTokenResponse:
    user = User(email=payload.email, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Username or email already exists")
    token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=token)


@app.post("/auth/login", response_model=AuthTokenResponse)
async def login(payload: AuthLoginRequest, db: AsyncSession = Depends(get_db)) -> AuthTokenResponse:
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=token)


@app.get("/posts", response_model=CursorPage)
async def list_posts(
    limit: int = 10,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> CursorPage:
    limit = max(1, min(limit, 50))

    # Very small cache window for hot feed queries
    cache_key = f"posts:limit={limit}:cursor={cursor or ''}"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        # Pydantic will coerce this back into the proper model
        return CursorPage(**cached)

    q = (
        select(Post)
        .options(selectinload(Post.author))
        .order_by(desc(Post.created_at), desc(Post.id))
        .limit(limit + 1)
    )
    if cursor:
        (created_at, post_id) = decode_cursor(cursor)
        # Fetch strictly older than cursor (created_at,id) tuple.
        q = q.where(
            (Post.created_at < created_at)
            | ((Post.created_at == created_at) & (Post.id < post_id))
        )

    result = await db.execute(q)
    posts = list(result.scalars().all())

    has_more = len(posts) > limit
    posts = posts[:limit]

    # Comment counts in one query
    counts = {}
    if posts:
        post_ids = [p.id for p in posts]
        c_result = await db.execute(
            select(Comment.post_id, func.count(Comment.id)).where(Comment.post_id.in_(post_ids)).group_by(Comment.post_id)
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
    # Cache for a few seconds to smooth bursts; we don't do fine-grained invalidation yet.
    await cache_set_json(cache_key, page.model_dump(mode="json"), ttl_seconds=5)
    return page


@app.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    payload: PostCreateRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> PostResponse:
    # Basic validation based on type
    if payload.type == PostType.text and not payload.body:
        raise HTTPException(status_code=400, detail="body is required for text posts")
    if payload.type == PostType.link and not payload.link_url:
        raise HTTPException(status_code=400, detail="link_url is required for link posts")
    if payload.type == PostType.photo and not payload.image_url:
        raise HTTPException(status_code=400, detail="image_url is required for photo posts")

    author_name = user.username if user else (payload.author_name or "Guest")

    post = Post(
        type=payload.type,
        title=payload.title,
        body=payload.body,
        link_url=str(payload.link_url) if payload.link_url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        author_id=user.id if user else None,
        author_name=None if user else author_name,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

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


@app.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
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


@app.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: uuid.UUID,
    payload: CommentCreateRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> CommentResponse:
    # Ensure post exists
    p = await db.execute(select(Post.id).where(Post.id == post_id))
    if not p.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    author_name = user.username if user else (payload.author_name or "Guest")
    comment = Comment(
        post_id=post_id,
        body=payload.body,
        author_id=user.id if user else None,
        author_name=None if user else author_name,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        created_at=comment.created_at,
        body=comment.body,
        author_name=author_name,
    )


# “Library” endpoints (MVP: static seed data; later: tables + CRUD)
@app.get("/library/recipes", response_model=list[Recipe])
async def recipes() -> list[Recipe]:
    cache_key = "library:recipes"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return [Recipe(**item) for item in cached]

    data = [
        Recipe(id="old-fashioned", title="Old Fashioned", tags=["classic", "whiskey"]),
        Recipe(id="negroni", title="Negroni", tags=["classic", "gin"]),
        Recipe(id="daiquiri", title="Daiquiri", tags=["rum", "sour"]),
    ]
    await cache_set_json(cache_key, [r.model_dump(mode="json") for r in data], ttl_seconds=60)
    return data


@app.get("/library/places", response_model=list[Place])
async def places() -> list[Place]:
    cache_key = "library:places"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return [Place(**item) for item in cached]

    data = [
        Place(id="favorite-local", name="Your Favorite Local", city="(add city)"),
        Place(id="hotel-bar", name="A Great Hotel Bar", city="(add city)"),
    ]
    await cache_set_json(cache_key, [p.model_dump(mode="json") for p in data], ttl_seconds=60)
    return data


@app.get("/library/history", response_model=list[HistoryEntry])
async def history() -> list[HistoryEntry]:
    cache_key = "library:history"
    cached = await cache_get_json(cache_key)
    if cached is not None:
        return [HistoryEntry(**item) for item in cached]

    data = [
        HistoryEntry(id="ice", title="Why ice quality matters"),
        HistoryEntry(id="bitters", title="Bitters: the bartender’s spice rack"),
    ]
    await cache_set_json(cache_key, [h.model_dump(mode="json") for h in data], ttl_seconds=60)
    return data


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    response = await call_next(request)
    response.headers["x-app"] = "bartender-journal"
    return response

