from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.metrics import AUTH_LOGINS
from app.models import User
from app.schemas import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
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


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: AuthLoginRequest, db: AsyncSession = Depends(get_db)) -> AuthTokenResponse:
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        AUTH_LOGINS.labels(outcome="failure").inc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    AUTH_LOGINS.labels(outcome="success").inc()
    token = create_access_token(str(user.id))
    return AuthTokenResponse(access_token=token)
