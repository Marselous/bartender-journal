"""Prometheus business metrics and auto-instrumentation setup."""
from __future__ import annotations

from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()

POSTS_CREATED = Counter(
    "bartender_posts_created",
    "Number of posts created",
    labelnames=("type",),
)
COMMENTS_CREATED = Counter(
    "bartender_comments_created",
    "Number of comments created",
)
AUTH_LOGINS = Counter(
    "bartender_auth_logins",
    "Authentication login attempts",
    labelnames=("outcome",),
)
FEED_CACHE_REQUESTS = Counter(
    "bartender_feed_cache_requests",
    "Feed cache lookups",
    labelnames=("outcome",),
)
POST_CREATE_SECONDS = Histogram(
    "bartender_post_create_seconds",
    "Post creation latency in seconds",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)
COMMENT_CREATE_SECONDS = Histogram(
    "bartender_comment_create_seconds",
    "Comment creation latency in seconds",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)
