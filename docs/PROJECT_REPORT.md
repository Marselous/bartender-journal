# Bartender Journal — Project Report

> A full-stack, DevOps-portfolio-grade web application deployable with a single command.
> This document is both a personal cheat sheet and an HR-facing technical overview.

---

## Table of Contents

1. [What We Built](#1-what-we-built)
2. [System Architecture](#2-system-architecture)
3. [Backend Deep Dive](#3-backend-deep-dive)
4. [Database Design](#4-database-design)
5. [Authentication & Security](#5-authentication--security)
6. [Caching Strategy](#6-caching-strategy)
7. [Pagination](#7-pagination)
8. [Asynchronous Task Queue](#8-asynchronous-task-queue)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Kubernetes Infrastructure](#10-kubernetes-infrastructure)
11. [Scalability & Flexibility](#11-scalability--flexibility)
12. [Frontend](#12-frontend)
13. [Local Development](#13-local-development)
14. [Known Gaps & Roadmap](#14-known-gaps--roadmap)
15. [Full Technology Stack at a Glance](#15-full-technology-stack-at-a-glance)

---

## 1. What We Built

**Bartender Journal** is a community board for bartenders — a place to post shift notes, cocktail links, and photos, and comment on each other's content. It also serves a small cocktail library (recipes, places, historical entries).

The product is intentionally **production-shaped**: it goes beyond a tutorial CRUD app and demonstrates the full set of decisions a senior engineer makes in a real system — async I/O, caching, auth, background tasks, schema migrations, Kubernetes deployment, Prometheus metrics, distributed tracing, and automated traffic generation.

Everything runs locally in minikube with one command:

```bash
./scripts/minikube_init.sh
```

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│    └─ http://<minikube-ip>:30000  (Frontend / NGINX)            │
│         │  Vanilla JS — no framework, no build step             │
│         │  All API calls via fetch() to backend NodePort        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend  http://<minikube-ip>:30001  (FastAPI / Uvicorn)        │
│    ├── /healthz          Health check                           │
│    ├── /auth/register    User registration                      │
│    ├── /auth/login       JWT login                              │
│    ├── /posts            Feed (GET, paginated) + create (POST)  │
│    ├── /posts/{id}/comments  Comments (GET + POST)              │
│    ├── /library/*        Recipes, Places, History               │
│    ├── /metrics          Prometheus scrape endpoint             │
│    └── /admin            SQLAdmin CRUD panel                    │
│                                                                 │
│    Depends on:                                                  │
│      ├── PostgreSQL :5432  (ClusterIP — internal only)          │
│      └── Redis      :6379  (ClusterIP — internal only)          │
└─────────────────────────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────┐       ┌──────────────────────┐
│   PostgreSQL 16  │       │    Redis 7-alpine     │
│   StatefulSet    │       │    Deployment         │
│   PVC 2Gi        │       │    Cache + Broker     │
└──────────────────┘       └──────────────────────┘
                                     │
                                     ▼
                           ┌──────────────────────┐
                           │   Celery Worker       │
                           │   (same backend image)│
                           │   reads broker queue  │
                           └──────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Observability                                                  │
│    Prometheus :30090  — scrapes /metrics every 15s              │
│    Grafana    :30300  — pre-built dashboard (4 panels)          │
│                                                                 │
│  Load generation                                                │
│    traffic-generator Deployment  — continuous mixed traffic     │
│    3 CronJobs — read latency, write throughput, metrics snap    │
└─────────────────────────────────────────────────────────────────┘
```

**Key architectural decisions:**
- All internal services communicate via Kubernetes ClusterIP (not exposed externally).
- Only three ports are exposed via NodePort: 30000 (frontend), 30001 (API), 30090 (Prometheus), 30300 (Grafana).
- Backend and Celery worker share the same Docker image — just a different command override in the k8s manifest.

---

## 3. Backend Deep Dive

**Framework:** FastAPI 0.115.8 on Python 3.12, served by Uvicorn (async ASGI).

The entry point (`main.py`) is a thin ~50-line wiring file. All business logic lives in five route modules:

| Module | Prefix | Responsibility |
|--------|--------|----------------|
| `health.py` | `/healthz` | Liveness probe — returns `{"ok": true, "ts": "<utc>"}` |
| `auth.py` | `/auth` | Register + login, issues JWT |
| `posts.py` | `/posts` | Feed listing (paginated, cached) + post creation |
| `comments.py` | `/posts/{id}/comments` | Comment listing + creation |
| `library.py` | `/library` | Static seeded data (recipes, places, history), Redis-cached |

Supporting modules are single-responsibility:

| File | What it does |
|------|-------------|
| `security.py` | Argon2 hashing + JWT encode/decode |
| `cache.py` | Async Redis wrapper with graceful degradation |
| `metrics.py` | Prometheus counter/histogram definitions |
| `pagination.py` | Cursor encode/decode (base64url + JSON) |
| `dependencies.py` | FastAPI `Depends` callables for optional auth |
| `helpers.py` | Author name resolution (user vs. guest) |
| `constants.py` | Cache key templates, TTLs, app name, OTel service name |
| `settings.py` | Pydantic-settings — reads env vars / `.env` file |
| `worker.py` | Celery app definition + task stubs |
| `admin.py` | SQLAdmin configuration (Users, Posts, Comments) |
| `middleware.py` | Custom ASGI middleware (adds `X-App` response header) |

### Example: a post creation request, end to end

```
POST /posts
{
  "type": "text",
  "title": "Shift notes",
  "body":  "New citrus prep worked great.",
  "author_name": "Alice"
}
```

1. FastAPI validates the JSON against `PostCreateRequest` (Pydantic v2). If `type=text` and no `body`, raises 400.
2. `get_optional_user` dependency inspects the `Authorization` header. No token present → `user = None`.
3. `resolve_author_name(user=None, payload_name="Alice")` → stores `"Alice"` in `author_name`, `author_id = NULL`.
4. SQLAlchemy async session inserts a new `Post` row, commits, refreshes.
5. Prometheus counter `bartender_posts_created{type="text"}` increments; histogram records write latency.
6. Returns `PostResponse` with 201.

---

## 4. Database Design

**Database:** PostgreSQL 16, accessed via asyncpg with SQLAlchemy 2.0 async ORM.

Three tables:

```
users
  id            UUID  PK
  email         VARCHAR(320)  UNIQUE  INDEX
  username      VARCHAR(50)   UNIQUE  INDEX
  password_hash VARCHAR(255)
  created_at    TIMESTAMPTZ   DEFAULT now()

posts
  id          UUID  PK
  created_at  TIMESTAMPTZ  INDEX  DEFAULT now()
  type        ENUM('text','link','photo')
  title       VARCHAR(140)   nullable
  body        TEXT           nullable
  link_url    VARCHAR(2048)  nullable
  image_url   VARCHAR(2048)  nullable
  author_id   UUID  FK→users.id  ON DELETE SET NULL  nullable
  author_name VARCHAR(80)    nullable

comments
  id       UUID  PK
  post_id  UUID  FK→posts.id  ON DELETE CASCADE  INDEX
  created_at TIMESTAMPTZ  INDEX  DEFAULT now()
  body       TEXT  NOT NULL
  author_id  UUID  FK→users.id  ON DELETE SET NULL  nullable
  author_name VARCHAR(80)  nullable
```

**Notable decisions:**

- `author_id` is nullable on both `posts` and `comments` — this is how guest posting works. When a user deletes their account (or is deleted), their posts/comments stay but `author_id` is set to NULL (`ON DELETE SET NULL`). When a post is deleted, all its comments cascade-delete (`ON DELETE CASCADE`).
- PostgreSQL native `ENUM` type for `post_type` — enforced at the DB level.
- `created_at` is indexed on both `posts` and `comments` — critical for cursor pagination performance.

**Migrations:** Alembic, single initial revision (`0001_init`). Applied automatically by a Kubernetes **init container** before the backend pod starts, so migrations always run before the API accepts traffic.

---

## 5. Authentication & Security

### Auth model: optional JWT

This system supports two user modes simultaneously:

| Mode | How it works | Stored as |
|------|-------------|-----------|
| **Guest** | No token, provides `author_name` in request body | `author_id = NULL`, `author_name = "Alice"` |
| **Registered** | Bearer JWT in `Authorization` header | `author_id = <uuid>`, username pulled from DB |

This design means the wall is always open — registration is never a barrier to participation.

### Password hashing — Argon2

```python
# security.py
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)   # produces $argon2id$... hash

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)
```

Argon2 (specifically Argon2id) is the winner of the 2015 Password Hashing Competition. It is memory-hard, GPU-resistant, and the current industry recommendation over bcrypt or scrypt. Using `passlib` means algorithm upgrades are handled automatically via the `deprecated="auto"` flag.

### JWT — HS256, 24-hour expiry

```python
# security.py — what a token payload looks like
{
  "sub": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # user UUID
  "iat": 1704067200,   # issued at (Unix timestamp)
  "exp": 1704153600    # expires at (24h later)
}
```

Tokens are signed with `JWT_SECRET_KEY` (env var). The `get_optional_user` dependency tries to decode the bearer token; on any failure (expired, tampered, missing) it returns `None` silently — the request continues as a guest rather than rejecting it.

### XSS prevention (frontend)

All user-generated content is passed through `escapeHtml()` before any DOM insertion:

```js
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c])
  );
}
// Example: posting <script>alert(1)</script> as author_name
// Rendered as: &lt;script&gt;alert(1)&lt;/script&gt; — inert text
```

No `innerHTML` is ever used with raw API strings.

### Current security gaps (known, documented)

| Gap | Risk | Mitigation plan |
|-----|------|-----------------|
| JWT secret is `dev-change-me` in k8s Secret | Critical in production | Rotate before any real deployment |
| No rate limiting on POST endpoints | Spam, brute-force | Add `slowapi` (Redis already present) |
| Admin panel has no auth | Internal data exposed | Add `sqladmin` AuthenticationBackend |
| Grafana default `admin/admin` | Dashboard access | Change credentials on deploy |

---

## 6. Caching Strategy

**Cache layer:** Redis 7-alpine, accessed via async `redis-py`.

### Graceful degradation — the key design

If Redis is unreachable (pod down, network issue, timeout), every cache operation returns `None` (cache miss) without raising an exception. The application continues serving requests from PostgreSQL. This means Redis is a performance optimisation, not a single point of failure.

```python
# cache.py — the entire resilience pattern
async def cache_get_json(key: str) -> Any | None:
    client = get_redis()
    if not client:
        return None          # Redis disabled via empty REDIS_URL
    try:
        value = await client.get(key)
    except RedisError:
        return None          # Redis down — gracefully degrade to miss
    ...
```

### What is cached

| Endpoint | Cache key | TTL | Reason |
|----------|-----------|-----|--------|
| `GET /posts?limit=10&cursor=` | `feed:10:` | **5 seconds** | Feed is read far more than written; short TTL keeps freshness |
| `GET /posts?limit=10&cursor=<x>` | `feed:10:<cursor>` | 5 seconds | Each page cached independently |
| `GET /library/recipes` | `library:recipes` | **60 seconds** | Static seeded data, rarely changes |
| `GET /library/places` | `library:places` | 60 seconds | Same |
| `GET /library/history` | `library:history` | 60 seconds | Same |

### Cache hit tracking

Every feed lookup records itself as a Prometheus counter:

```python
if cached is not None:
    FEED_CACHE_REQUESTS.labels(outcome="hit").inc()
    return CursorPage(**cached)
FEED_CACHE_REQUESTS.labels(outcome="miss").inc()
```

This means you can plot cache hit rate in Grafana and see the effect of traffic patterns on Redis efficiency.

---

## 7. Pagination

The feed uses **keyset / cursor pagination**, not `OFFSET`.

### Why not OFFSET?

`OFFSET 100` tells PostgreSQL to scan and discard 100 rows before returning results. On a large table this gets slower as the user pages deeper. Cursor pagination jumps directly to the correct position using an index.

### How it works

```
First request:  GET /posts?limit=10
  → returns 10 posts + next_cursor = "eyJjcmVhdGVkX2..."

Second request: GET /posts?limit=10&cursor=eyJjcmVhdGVkX2...
  → cursor decodes to {"created_at": "2026-01-15T10:30:00Z", "id": "abc-123"}
  → SQL:  WHERE (created_at < '2026-01-15T10:30:00Z')
            OR  (created_at = '2026-01-15T10:30:00Z' AND id < 'abc-123')
          ORDER BY created_at DESC, id DESC
          LIMIT 11   ← fetch one extra to detect if there's a next page
```

The cursor is a base64url-encoded JSON blob containing the `created_at` and `id` of the last item seen. Both fields together form a stable, unique sort key even when multiple posts share the same timestamp.

---

## 8. Asynchronous Task Queue

**Queue:** Celery, using Redis as both broker and result backend.

The worker runs as a separate Kubernetes Deployment (same Docker image, different command):

```yaml
# k8s/worker.yaml
command: ["celery", "-A", "app.worker.celery_app", "worker", "-l", "info"]
```

Two tasks are defined as architecture stubs:

```python
# worker.py
@celery_app.task(name="tasks.process_image")
def process_image(post_id: str, image_url: str | None) -> dict:
    # Real system: download image → resize → re-upload to S3/MinIO
    # → update post.image_url with the processed URL
    logger.info("Processing image for post %s: %s", post_id, image_url)
    return {"post_id": post_id, "image_url": image_url}

@celery_app.task(name="tasks.send_notification")
def send_notification(recipient: str, message: str) -> dict:
    # Real system: POST to SendGrid / Mailgun / Slack webhook
    logger.info("Sending notification to %s: %s", recipient, message)
    return {"recipient": recipient}
```

**Current state:** tasks are defined and the worker runs, but the API routes do not yet call `.delay()` to dispatch them. Dispatching `process_image` on photo post creation is the top P1 item on the roadmap.

**Why this architecture matters:** separating image processing from the HTTP request cycle prevents slow image downloads/resizes from blocking API response time. The POST /posts endpoint responds immediately; processing happens in the background.

---

## 9. Monitoring & Observability

Three complementary systems are deployed.

### Prometheus — metrics

Prometheus scrapes the backend every 15 seconds at `/metrics`.

**Auto-instrumented HTTP metrics** (from `prometheus-fastapi-instrumentator`):

| Metric | Type | Example query |
|--------|------|---------------|
| `http_requests_total` | Counter | Rate of requests by endpoint |
| `http_request_duration_seconds` | Histogram | p95 latency by handler |

**Custom business metrics** (defined in `metrics.py`):

| Metric | Type | Labels | What it tells you |
|--------|------|--------|-------------------|
| `bartender_posts_created_total` | Counter | `type` | How many text/link/photo posts, over time |
| `bartender_comments_created_total` | Counter | — | Comment velocity |
| `bartender_auth_logins_total` | Counter | `outcome` | Login success vs. failure rate (detect brute-force) |
| `bartender_feed_cache_requests_total` | Counter | `outcome` | Cache hit ratio |
| `bartender_post_create_seconds` | Histogram | — | Actual DB write latency distribution |
| `bartender_comment_create_seconds` | Histogram | — | Same for comments |

**Example Prometheus query** — cache hit rate over last 5 minutes:

```promql
rate(bartender_feed_cache_requests_total{outcome="hit"}[5m])
/
rate(bartender_feed_cache_requests_total[5m])
```

### Grafana — dashboards

Pre-provisioned dashboard "Bartender Journal API Overview" with 4 panels, auto-refreshed every 10 seconds:

1. **Request rate** — `rate(http_requests_total[1m])` grouped by handler + method
2. **p95 latency** — `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
3. **5xx error rate** — `rate(http_requests_total{status=~"5.."}[1m])`
4. **Traffic by status code** — breakdown of 2xx / 4xx / 5xx

Datasource is pre-provisioned via ConfigMap — no manual setup required after deploy.

### OpenTelemetry — distributed tracing

FastAPI is auto-instrumented via `FastAPIInstrumentor`. Every HTTP request produces a trace span that includes handler name, HTTP method, status code, and duration. Traces are exported via OTLP HTTP to `http://localhost:4318`.

```python
# main.py
resource = Resource.create({"service.name": "bartender-journal-api"})
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)
```

**Current state:** the SDK and exporter are wired. A collector (e.g. Jaeger, Tempo) is not yet deployed in the cluster, so traces are exported but not yet visualised. Deploying the collector is a P2 roadmap item.

### In-cluster load generation

A `traffic-generator` Deployment runs continuously, simulating realistic mixed traffic:

- Every 0.8s: hits `/healthz` + `GET /posts`
- 35% probability: `POST /posts` (creates a text post as `k8s-load-bot`)
- 25% probability: `POST /posts/{id}/comments` on the latest post

Three CronJobs run periodic load patterns:

| Job | Schedule | Purpose |
|-----|----------|---------|
| `task-read-latency` | Every 2 min | 60 read requests — measures sustained read latency |
| `task-write-throughput` | Every 3 min | 30 write requests — measures write throughput |
| `task-metrics-snapshot` | Every 4 min | Pulls `/metrics`, logs first 40 lines |

This means **Grafana always has data to show**, even with no real users — essential for a portfolio demo.

---

## 10. Kubernetes Infrastructure

All manifests live in `k8s/`, applied as a single Kustomize bundle (`kubectl apply -k k8s/`), all in the `bartender` namespace.

### Component summary

| Component | Kind | Image | Exposed |
|-----------|------|-------|---------|
| PostgreSQL | StatefulSet | `postgres:16` | ClusterIP :5432 |
| Redis | Deployment | `redis:7-alpine` | ClusterIP :6379 |
| Backend | Deployment | `bartender-backend:local` | NodePort 30001 |
| Frontend | Deployment | `bartender-frontend:local` | NodePort 30000 |
| Celery worker | Deployment | `bartender-backend:local` | None |
| Prometheus | Deployment | `prom/prometheus:v2.55.1` | NodePort 30090 |
| Grafana | Deployment | `grafana/grafana:11.2.2` | NodePort 30300 |
| traffic-generator | Deployment | `python:3.12-alpine` | None |
| CronJobs (3) | CronJob | `curlimages/curl:8.9.1` | None |

### Zero-downtime migration pattern

The backend Deployment includes an **init container** that runs Alembic migrations before the main container starts:

```yaml
initContainers:
  - name: run-migrations
    image: bartender-backend:local
    command: ["python", "-m", "app.run_migrations"]
```

This guarantees: DB schema is always up to date before the API starts accepting traffic. On a rolling update, the new pod's init container runs migrations, then the new pod becomes ready, then old pods are terminated.

### Health probes

The backend pod has both readiness and liveness probes pointing at `/healthz`:

```yaml
readinessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 5
  periodSeconds: 5

livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 15
  periodSeconds: 10
```

Kubernetes will not send traffic to a backend pod until `/healthz` returns 200, and will restart any pod that starts returning errors — matching production-grade behaviour.

### Resource management

Redis is the only component with explicit resource constraints set:

```yaml
resources:
  requests: { cpu: 50m, memory: 64Mi }
  limits:   { cpu: 250m, memory: 256Mi }
```

All other deployments inherit minikube defaults — appropriate for a local dev cluster.

---

## 11. Scalability & Flexibility

### What scales horizontally today

| Component | How |
|-----------|-----|
| Backend | Increase `replicas` in `backend.yaml`; stateless, all state in Postgres + Redis |
| Celery workers | Increase `replicas` in `worker.yaml`; workers compete for tasks from shared Redis queue |
| Frontend | Increase `replicas`; pure static files, fully stateless |

The backend is fully stateless by design:
- No in-process session storage (JWT is the session)
- No in-process cache (all cache is in Redis)
- Each request gets a fresh DB connection from the async pool

### What does not scale horizontally yet

| Component | Current limit | Fix |
|-----------|--------------|-----|
| PostgreSQL | Single StatefulSet replica (read/write) | Add read replicas or migrate to managed DB |
| Redis | Single instance | Redis Sentinel or Cluster mode |
| Prometheus | emptyDir (ephemeral) | Add PVC or use remote write to Thanos/Cortex |

### Flexibility — what is configurable without code changes

Everything sensitive or environment-specific is an environment variable read by `pydantic-settings`:

```
DATABASE_URL          — swap to any PostgreSQL-compatible URL
REDIS_URL             — set to empty string to disable caching entirely
JWT_SECRET_KEY        — rotate without touching code
JWT_ACCESS_TOKEN_EXPIRES_MINUTES  — adjust token lifetime
CORS_ORIGINS          — lockdown to specific frontend origins in production
ENVIRONMENT           — shown in logs; switch dev/staging/prod
```

The CORS middleware accepts `["*"]` for local dev but can be locked to a specific origin list for production with a single env var change.

### Flexibility — pluggable components

| Component | Current | Swap-in alternative |
|-----------|---------|---------------------|
| Cache | Redis | Memcached, DragonflyDB |
| Task broker | Redis | RabbitMQ (change `broker_url`) |
| Object storage | URL-only | MinIO, AWS S3 (add task dispatch) |
| Tracing backend | OTLP → nowhere | Jaeger, Tempo, Datadog (just deploy collector) |
| Auth | JWT HS256 | RS256 (swap keys), OAuth2/OIDC (add provider) |

---

## 12. Frontend

**Technology:** Vanilla HTML/CSS/JS. No framework, no bundler, no CDN dependencies. NGINX 1.27 Alpine serves three static files.

After the redesign (`update/plan-frontend` branch), the frontend is split into:

| File | Role |
|------|------|
| `index.html` | Page structure only (~175 lines) |
| `style.css` | Design system — tokens, glassmorphism, animations (~380 lines) |
| `app.js` | All application logic (~480 lines) |

**Design system highlights:**
- Dark background with three-layer radial gradient (gold + blue + purple)
- Glassmorphism plates (`backdrop-filter: blur(20px) saturate(160%)`)
- Responsive hero with `clamp(52px, 7vw, 80px)` headline
- Post cards with type badges, avatar initials, relative timestamps
- Skeleton loaders (shimmer animation) while feed loads
- Library panel renders items as cards with tag chips

**Security:** All user content passed through `escapeHtml()` before DOM insertion. No `innerHTML` of raw API strings anywhere.

**API integration pattern:**
```js
// All API calls go through fetchJson — adds auth header automatically
async function fetchJson(url, opts = {}) {
  const headers = { "content-type": "application/json" };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(url, { ...opts, headers });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

JWT is stored in `localStorage` and sent on every request automatically. No page reloads required — the UI updates in place.

---

## 13. Local Development

### One-command deploy

```bash
./scripts/minikube_init.sh
```

This script:
1. Checks prerequisites (minikube, kubectl, docker)
2. Starts minikube if not running
3. Builds both images into minikube (no registry push)
4. Applies `kubectl apply -k k8s/`
5. Restarts deployments to pick up fresh images
6. Waits up to 240s for each component to roll out
7. Prints service URLs

### Service URLs after deploy

```bash
IP=$(minikube ip)

Frontend:   http://$IP:30000
API:        http://$IP:30001
Prometheus: http://$IP:30090
Grafana:    http://$IP:30300   (admin / admin)
Admin:      http://$IP:30001/admin
```

### Quick API smoke test

```bash
IP=$(minikube ip)
BASE="http://$IP:30001"

# Health check
curl "$BASE/healthz"
# → {"ok":true,"ts":"2026-03-05T10:00:00Z"}

# Create a post as a guest
curl -s -X POST "$BASE/posts" \
  -H "content-type: application/json" \
  -d '{"type":"text","title":"Citrus prep","body":"New oleo saccharum — worth it.","author_name":"Alice"}' \
  | python3 -m json.tool

# Register a user
curl -s -X POST "$BASE/auth/register" \
  -H "content-type: application/json" \
  -d '{"email":"alice@bar.com","username":"alice","password":"secret123"}' \
  | python3 -m json.tool
# → {"access_token":"eyJ..."}

# Login and use the token
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H "content-type: application/json" \
  -d '{"username":"alice","password":"secret123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a post as authenticated user
curl -s -X POST "$BASE/posts" \
  -H "content-type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"type":"link","title":"Best bitters guide","link_url":"https://example.com/bitters"}' \
  | python3 -m json.tool

# Read the feed (first page)
curl -s "$BASE/posts?limit=5" | python3 -m json.tool

# Add a comment (replace POST_ID)
curl -s -X POST "$BASE/posts/<POST_ID>/comments" \
  -H "content-type: application/json" \
  -d '{"body":"Great find!","author_name":"Bob"}' \
  | python3 -m json.tool
```

### Rebuild after code change

```bash
# Rebuild backend only
minikube image build -t bartender-backend:local ./backend
kubectl -n bartender rollout restart deploy/backend deploy/worker

# Rebuild frontend only
minikube image build -t bartender-frontend:local ./frontend
kubectl -n bartender rollout restart deploy/frontend

# Watch rollout
kubectl -n bartender rollout status deploy/backend
```

---

## 14. Known Gaps & Roadmap

### P1 — High portfolio impact

| # | Item | What's needed |
|---|------|--------------|
| 1 | **Dispatch Celery tasks from API** | Call `process_image.delay(post_id, image_url)` in `POST /posts` for photo type |
| 2 | **Persist library data in DB** | Add `Recipe`, `Place`, `HistoryEntry` ORM models + Alembic migration + CRUD routes |
| 3 | **Frontend redesign** | Applied on `update/plan-frontend` branch — hero, glass cards, library rendering |

### P2 — Correctness

| # | Item | What's needed |
|---|------|--------------|
| 4 | **Rate limiting** | `slowapi` on POST endpoints; Redis is already present |
| 5 | **Prometheus PVC** | Replace `emptyDir` with PVC so metrics survive pod restarts |
| 6 | **OTel collector** | Deploy Jaeger or Grafana Tempo to actually receive and visualise traces |

### P3 — Hardening

| # | Item | What's needed |
|---|------|--------------|
| 7 | **Test suite** | `pytest-asyncio` + `httpx.AsyncClient` against in-memory SQLite |
| 8 | **Admin auth** | `sqladmin` `AuthenticationBackend` — even a hardcoded password beats open access |
| 9 | **JWT secret rotation** | Document + script the process; use k8s Secret with `secretKeyRef` |

---

## 15. Full Technology Stack at a Glance

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend framework | FastAPI | 0.115.8 | Async HTTP API |
| ASGI server | Uvicorn | 0.34.0 | Runs FastAPI |
| ORM | SQLAlchemy (async) | 2.0.38 | Database access |
| DB driver | asyncpg | 0.30.0 | PostgreSQL async adapter |
| Schema migrations | Alembic | 1.14.1 | Versioned DB migrations |
| Validation | Pydantic v2 | 2.10.6 | Request/response schemas |
| Settings | pydantic-settings | 2.8.0 | Env var configuration |
| Auth tokens | python-jose | 3.3.0 | JWT encode/decode |
| Password hashing | passlib + Argon2 | 1.7.4 | Secure password storage |
| Cache client | redis-py (async) | latest | Redis cache + Celery broker |
| Task queue | Celery | latest | Background job execution |
| Admin UI | SQLAdmin | latest | Browser CRUD panel |
| HTTP metrics | prometheus-fastapi-instrumentator | latest | Auto-instruments FastAPI |
| Custom metrics | prometheus-client | latest | Business counters/histograms |
| Tracing | OpenTelemetry SDK + OTLP exporter | latest | Distributed trace export |
| Database | PostgreSQL | 16 | Primary data store |
| Cache / broker | Redis | 7-alpine | Cache + Celery transport |
| Frontend server | NGINX | 1.27-alpine | Serves static files |
| Frontend | Vanilla HTML/CSS/JS | — | No framework, no build step |
| Orchestration | Kubernetes (minikube) | — | Local cluster |
| Manifest management | Kustomize | — | `kubectl apply -k k8s/` |
| Monitoring | Prometheus | v2.55.1 | Metrics storage |
| Dashboards | Grafana | 11.2.2 | Visualisation |
| Python version | CPython | 3.12 | Runtime |
| Base images | python:3.12-slim, nginx:1.27-alpine, postgres:16, redis:7-alpine | — | Container bases |
