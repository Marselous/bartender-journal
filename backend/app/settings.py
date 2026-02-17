from __future__ import annotations

import json

from pydantic import AnyUrl
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Bartender Journal API"
    environment: str = "dev"

    cors_origins: list[str] = ["*"]

    database_url: str = "postgresql+asyncpg://bartender:bartender@postgres:5432/bartender"

    jwt_secret_key: str = "dev-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60 * 24

    public_base_url: AnyUrl | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v):
        if v is None:
            return ["*"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return ["*"]
            # Allow JSON list: '["http://localhost:3000"]'
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except Exception:
                    pass
            # Allow comma-separated: "http://a, http://b"
            return [p.strip() for p in s.split(",") if p.strip()]
        return ["*"]


settings = Settings()

