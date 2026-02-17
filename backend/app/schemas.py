from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class PostType(StrEnum):
    text = "text"
    link = "link"
    photo = "photo"


class UserPublic(BaseModel):
    id: uuid.UUID
    username: str
    created_at: datetime


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PostCreateRequest(BaseModel):
    type: PostType
    title: str | None = Field(default=None, max_length=140)
    body: str | None = None
    link_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    author_name: str | None = Field(default=None, max_length=80)


class PostResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    type: PostType
    title: str | None
    body: str | None
    link_url: str | None
    image_url: str | None
    author_name: str | None
    comment_count: int


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    author_name: str | None = Field(default=None, max_length=80)


class CommentResponse(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    created_at: datetime
    body: str
    author_name: str | None


class CursorPage(BaseModel):
    items: list[PostResponse]
    next_cursor: str | None = None


class Recipe(BaseModel):
    id: str
    title: str
    tags: list[str] = []


class Place(BaseModel):
    id: str
    name: str
    city: str | None = None


class HistoryEntry(BaseModel):
    id: str
    title: str

