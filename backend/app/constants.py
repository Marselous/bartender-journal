"""Centralized constants for cache keys, TTLs, and app defaults."""

# Cache key patterns
FEED_CACHE_KEY_TEMPLATE = "posts:limit={limit}:cursor={cursor}"
LIBRARY_RECIPES_CACHE_KEY = "library:recipes"
LIBRARY_PLACES_CACHE_KEY = "library:places"
LIBRARY_HISTORY_CACHE_KEY = "library:history"

# Cache TTLs (seconds)
FEED_CACHE_TTL_SECONDS = 5
LIBRARY_CACHE_TTL_SECONDS = 60

# Default author name for anonymous users
DEFAULT_AUTHOR_NAME = "Guest"

# OpenTelemetry
OTEL_SERVICE_NAME = "bartender-journal-api"

# Custom response header
APP_HEADER_NAME = "x-app"
APP_HEADER_VALUE = "bartender-journal"
