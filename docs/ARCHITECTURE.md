# Bartender Journal — Architecture Reference

---

## 1. What is this project?

**Bartender Journal** is a full-stack, DevOps-portfolio-grade web application. It is a public "bartender wall" — a community board where anyone (authenticated or guest) can post shift notes, cocktail recipes, links, or photos, and comment on each other's content. It also includes a small static library of recipes, places, and history entries.

The app is intentionally **production-shaped**: async Python backend, PostgreSQL persistence, Redis caching, JWT auth (optional), Kubernetes manifests, Prometheus metrics, OpenTelemetry tracing, Grafana dashboards, a Celery worker, and a continuous traffic generator — all deployable with a single script on minikube.

---

## 2. Repository layout

```
bartender-journal/
├── backend/                  # FastAPI API server
│   ├── app/
│   │   ├── main.py           # Thin entry point — wires routers, middleware, admin, OTel
│   │   ├── routes/           # FastAPI APIRouter modules
│   │   │   ├── health.py     # GET /healthz
│   │   │   ├── auth.py       # POST /auth/register, /auth/login
│   │   │   ├── posts.py      # GET/POST /posts
│   │   │   ├── comments.py   # GET/POST /posts/{id}/comments
│   │   │   └── library.py    # GET /library/recipes,places,history
│   │   ├── models.py         # SQLAlchemy ORM models (User, Post, Comment)
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── db.py             # Async SQLAlchemy engine + session factory
│   │   ├── cache.py          # Redis helpers (graceful degradation)
│   │   ├── security.py       # JWT creation/decoding, Argon2 password hashing
│   │   ├── settings.py       # Pydantic Settings (env / .env file)
│   │   ├── worker.py         # Celery app + placeholder async tasks
│   │   ├── admin.py          # SQLAdmin panel configuration
│   │   ├── metrics.py        # Prometheus business metrics definitions
│   │   ├── constants.py      # Cache keys, TTLs, app defaults
│   │   ├── pagination.py     # Cursor encode/decode utilities
│   │   ├── dependencies.py   # FastAPI dependency callables (auth)
│   │   ├── helpers.py        # Shared helpers (timestamps, author resolution)
│   │   ├── middleware.py      # Custom ASGI middleware
│   │   └── run_migrations.py # Alembic migration runner (used by init container)
│   ├── alembic/
│   │   └── versions/0001_init.py  # Initial DB migration (users, posts, comments)
│   ├── .env.example          # Environment variable template
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile            # python:3.12-slim, exposes port 8000
│
├── frontend/
│   ├── public/index.html     # Single-page app (vanilla JS, no framework)
│   └── Dockerfile            # nginx:1.27-alpine, exposes port 80
│
├── k8s/                      # Kubernetes manifests (Kustomize root)
│   ├── kustomization.yaml    # Lists all resources; namespace = bartender
│   ├── namespace.yaml
│   ├── postgres.yaml         # StatefulSet + PVC (2Gi) + ClusterIP Service
│   ├── backend.yaml          # Deployment + ConfigMap + Secret + NodePort (30001)
│   ├── frontend.yaml         # Deployment + NodePort (30000)
│   ├── redis.yaml            # Deployment + ClusterIP Service
│   ├── worker.yaml           # Celery worker Deployment
│   ├── observability/
│   │   ├── prometheus.yaml   # Prometheus Deployment + config + NodePort (30090)
│   │   └── grafana.yaml      # Grafana Deployment + datasource + dashboard + NodePort (30300)
│   └── load/
│       └── traffic.yaml      # traffic-generator Deployment + 3 CronJobs
│
├── scripts/
│   ├── minikube_init.sh      # One-command bootstrap: build images + apply k8s + wait
│   └── traffic_generator.py  # Local equivalent of the in-cluster load generator
│
├── docs/
│   ├── ARCHITECTURE.md       # Full architecture reference (this file)
│   ├── STAR-summary.md       # Resume-style STAR format summary
│   └── portfolio-feature-walkthrough.md  # Interview/demo runbook
│
├── .gitignore
├── LICENSE
└── CLAUDE.md                 # Project context for AI assistants
```

---

## 3. Tech stack

| Layer | Technology | Version |
|---|---|---|
| Backend framework | FastAPI | 0.115.8 |
| ASGI server | Uvicorn | 0.34.0 |
| ORM | SQLAlchemy (async) | 2.0.38 |
| DB driver | asyncpg | 0.30.0 |
| Migrations | Alembic | 1.14.1 |
| Validation | Pydantic v2 | 2.10.6 |
| Settings | pydantic-settings | 2.8.0 |
| Auth | python-jose (JWT) | 3.3.0 |
| Password hashing | passlib + Argon2 | 1.7.4 |
| Cache | redis-py (async) | latest |
| Task queue | Celery | latest |
| Admin UI | SQLAdmin | latest |
| Metrics | prometheus-fastapi-instrumentator | latest |
| Tracing | OpenTelemetry SDK + OTLP HTTP exporter | latest |
| Database | PostgreSQL | 16 |
| Cache/broker | Redis | 7-alpine |
| Frontend server | NGINX | 1.27-alpine |
| Frontend language | Vanilla HTML/CSS/JS | — |
| Orchestration | Kubernetes (minikube) + Kustomize | — |
| Monitoring | Prometheus | v2.55.1 |
| Dashboards | Grafana | 11.2.2 |
| Python version | Python | 3.12 |

---

## 4. Backend — deep dive

### 4.1 Entry point: `backend/app/main.py`

Thin wiring file (~50 lines) that assembles the application:

- Creates the `FastAPI` app instance
- Wires Prometheus auto-instrumentation (`app/metrics.py`)
- Sets up OpenTelemetry tracing (`OTEL_SERVICE_NAME` from `app/constants.py`)
- Attaches CORS middleware (origins from settings)
- Mounts SQLAdmin (`app/admin.py`)
- Includes 5 APIRouters from `app/routes/` (health, auth, posts, comments, library)
- Registers custom middleware (`app/middleware.py`)

All business logic lives in the route modules. Supporting concerns are extracted into dedicated files: `metrics.py`, `pagination.py`, `dependencies.py`, `helpers.py`, `constants.py`.

**Custom Prometheus business metrics**

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `bartender_posts_created` | Counter | `type` | Posts created per type (text/link/photo) |
| `bartender_comments_created` | Counter | — | Comments created |
| `bartender_auth_logins` | Counter | `outcome` | Login attempts (success/failure) |
| `bartender_feed_cache_requests` | Counter | `outcome` | Feed cache hit/miss |
| `bartender_post_create_seconds` | Histogram | — | Post write latency |
| `bartender_comment_create_seconds` | Histogram | — | Comment write latency |

**Cursor pagination**

The feed uses keyset/cursor pagination. Each cursor is a base64url-encoded JSON blob `{"created_at": "<ISO>", "id": "<UUID>"}`. Results are ordered `DESC created_at, DESC id` so the feed is stable even when posts share a timestamp.

**Auth flow**

Auth is entirely optional. Every post and comment endpoint accepts either:
- A valid `Authorization: Bearer <JWT>` token (sets `author_id` to the user's UUID, derives `author_name` from the user record), or
- No token at all (leaves `author_id` null, stores whatever `author_name` was provided, defaults to `"Guest"`).

### 4.2 API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/healthz` | Health check — returns `{"ok": true, "ts": "<utc>"}` |
| `POST` | `/auth/register` | Register (email, username, password) — returns JWT |
| `POST` | `/auth/login` | Login (username, password) — returns JWT |
| `GET` | `/posts` | Cursor-paginated feed (params: `limit`, `cursor`) |
| `POST` | `/posts` | Create post (type, title, body/link_url/image_url, author_name) |
| `GET` | `/posts/{post_id}/comments` | List all comments for a post |
| `POST` | `/posts/{post_id}/comments` | Add a comment to a post |
| `GET` | `/library/recipes` | Seeded recipe list (Redis-cached 60s) |
| `GET` | `/library/places` | Seeded places list (Redis-cached 60s) |
| `GET` | `/library/history` | Seeded history entries (Redis-cached 60s) |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint |
| `GET/POST` | `/admin/*` | SQLAdmin UI for Users, Posts, Comments |

### 4.3 Data models: `backend/app/models.py`

**`User`** — `users` table
- `id` UUID PK
- `email` String(320), unique, indexed
- `username` String(50), unique, indexed
- `password_hash` String(255)
- `created_at` timestamptz, server default `now()`
- Relationships: `posts` (one-to-many, cascade delete-orphan), `comments` (one-to-many, cascade delete-orphan)

**`Post`** — `posts` table
- `id` UUID PK
- `created_at` timestamptz, indexed
- `type` Enum `PostType` (`text` | `link` | `photo`)
- `title` String(140), nullable
- `body` Text, nullable
- `link_url` String(2048), nullable
- `image_url` String(2048), nullable
- `author_id` UUID FK → `users.id` ON DELETE SET NULL, nullable
- `author_name` String(80), nullable (used when no registered author)
- Relationships: `author` (User), `comments` (cascade delete-orphan)

**`Comment`** — `comments` table
- `id` UUID PK
- `post_id` UUID FK → `posts.id` ON DELETE CASCADE, indexed
- `created_at` timestamptz, indexed
- `body` Text, not null
- `author_id` UUID FK → `users.id` ON DELETE SET NULL, nullable
- `author_name` String(80), nullable
- Relationships: `post` (Post), `author` (User)

### 4.4 Caching: `backend/app/cache.py`

A thin wrapper around the async Redis client. If Redis is unavailable (connection refused, timeout, etc.), all cache operations silently degrade to a cache-miss — the application continues to function correctly without Redis.

- Feed (`GET /posts`): cached per `limit+cursor` combination, TTL = **5 seconds**.
- Library endpoints: cached per endpoint, TTL = **60 seconds**.

### 4.5 Security: `backend/app/security.py`

- Passwords hashed with **Argon2** via `passlib`.
- JWTs signed with **HS256**, secret from `JWT_SECRET_KEY` env var.
- Default token expiry: **24 hours** (configurable via `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`).
- `get_optional_user` dependency: decodes the bearer token if present, looks up the user by `sub` claim; returns `None` on any failure (not an error).

### 4.6 Settings: `backend/app/settings.py`

All configuration via environment variables (or `.env` file). Pydantic-settings handles parsing and defaults.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://bartender:bartender@postgres:5432/bartender` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection (set to empty string to disable cache) |
| `JWT_SECRET_KEY` | `dev-change-me` | **Must be changed in production** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | `1440` (24h) | Token lifetime |
| `CORS_ORIGINS` | `["*"]` | Accepts JSON list, comma-separated string, or `*` |
| `ENVIRONMENT` | `dev` | Shown in logs / admin |

### 4.7 Worker: `backend/app/worker.py`

Celery app using Redis as both broker and result backend. Two placeholder tasks demonstrate the architecture:

- `tasks.process_image(post_id, image_url)` — logs; real system would download/resize/re-upload to object storage.
- `tasks.send_notification(recipient, message)` — logs; real system would integrate with an email/webhook provider.

### 4.8 Database migrations: `backend/alembic/`

Single initial migration (`0001_init`) creates:
- `users` table + unique indexes on `email` and `username`
- `post_type` PostgreSQL enum type
- `posts` table + index on `created_at`
- `comments` table + indexes on `post_id` and `created_at`

Migrations are run automatically by a Kubernetes **init container** before the backend pod starts.

### 4.9 Dockerfile

Multi-stage-style but single stage (`python:3.12-slim`). Installs requirements, copies `app/`, `alembic/`, `alembic.ini`. Runs Uvicorn on `0.0.0.0:8000`.

---

## 5. Frontend — deep dive

### 5.1 Structure

A single file: `frontend/public/index.html` (~680 lines). Served by NGINX 1.27 Alpine with zero build tooling — no bundler, no framework, pure browser JS.

### 5.2 UI sections

- **Sticky nav** — brand name, section links (Wall / Library / About), Register/Sign in buttons, signed-in username badge.
- **Hero / About** — describes the project, tech-stack pills, and a **configurable API base URL** input. The URL is saved to `localStorage` and pinged via `/healthz` on save to verify connectivity.
- **New post form** — type selector (text / link / photo), optional title, author name, conditional body/link/image field. Posts to `POST /posts`.
- **Library panel** — buttons to load Recipes / Places / History from the backend and display raw JSON.
- **Infinite feed** — renders paginated post cards. Each card shows title, author, timestamp, comment count. Click "Comments" to expand: loads existing comments via `GET /posts/{id}/comments`, inline comment form posts via `POST /posts/{id}/comments`. "Load more" fetches the next cursor page.
- **Auth modals** — Register modal (`POST /auth/register`) and Sign in modal (`POST /auth/login`). On login, JWT is stored in `localStorage`; subsequent API calls send `Authorization: Bearer <token>`.
- **Toast notifications** — bottom-right non-blocking messages for success/error feedback.

### 5.3 Security note in frontend

All user-generated content is escaped with `escapeHtml()` before being inserted into the DOM, preventing XSS.

---

## 6. Kubernetes — deep dive

All manifests live in `k8s/` and are applied as a single Kustomize bundle (`kubectl apply -k k8s/`). Everything deploys into the `bartender` namespace.

### 6.1 Namespace

`k8s/namespace.yaml` — creates the `bartender` namespace.

### 6.2 PostgreSQL (`k8s/postgres.yaml`)

- **Kind**: StatefulSet (1 replica)
- **Image**: `postgres:16`
- **Storage**: PersistentVolumeClaim, 2Gi, `ReadWriteOnce`
- **Credentials**: Kubernetes Secret (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — all `bartender` for dev)
- **Health probes**: readiness + liveness via `pg_isready`
- **Service**: ClusterIP on port 5432 (name: `postgres`)

### 6.3 Redis (`k8s/redis.yaml`)

- **Kind**: Deployment (1 replica)
- **Image**: `redis:7-alpine`
- **Resources**: 50m CPU / 64Mi RAM requests; 250m CPU / 256Mi RAM limits
- **Service**: ClusterIP on port 6379 (name: `redis`)

### 6.4 Backend (`k8s/backend.yaml`)

- **Kind**: Deployment (1 replica)
- **Image**: `bartender-backend:local` (built into minikube)
- **Init container**: runs `python -m app.run_migrations` to apply Alembic migrations before the main container starts
- **Config**: `ConfigMap` `backend-config` provides `DATABASE_URL`, `CORS_ORIGINS`, `ENVIRONMENT`, `REDIS_URL`
- **Secret**: `backend-secret` provides `JWT_SECRET_KEY`
- **Health probes**: readiness (5s delay, 5s period) + liveness (15s delay, 10s period) both on `GET /healthz`
- **Service**: NodePort, port 8000, nodePort **30001**

### 6.5 Frontend (`k8s/frontend.yaml`)

- **Kind**: Deployment (1 replica)
- **Image**: `bartender-frontend:local` (NGINX + static HTML)
- **Service**: NodePort, port 80, nodePort **30000**

### 6.6 Celery Worker (`k8s/worker.yaml`)

- Same image as backend (`bartender-backend:local`)
- Command overridden to: `celery -A app.worker.celery_app worker -l info`
- Reads `DATABASE_URL` and `REDIS_URL` from the same ConfigMap

### 6.7 Prometheus (`k8s/observability/prometheus.yaml`)

- **Image**: `prom/prometheus:v2.55.1`
- **Scrape config** (15s interval):
  - `localhost:9090` (self)
  - `backend:8000` at `/metrics` (FastAPI metrics)
  - `backend:8000` at `/healthz` (health probe)
- **Service**: NodePort on port 9090, nodePort **30090**
- Prometheus data stored in `emptyDir` (ephemeral, resets on pod restart)

### 6.8 Grafana (`k8s/observability/grafana.yaml`)

- **Image**: `grafana/grafana:11.2.2`
- **Admin credentials**: `admin / admin` (defaults, change for production)
- **Pre-provisioned datasource**: Prometheus at `http://prometheus:9090`
- **Pre-provisioned dashboard**: "Bartender Journal API Overview" (4 panels):
  - Request rate by handler+method
  - p95 latency by handler+method
  - 5xx error rate by handler
  - Traffic by HTTP status code
- **Service**: NodePort on port 3000, nodePort **30300**

### 6.9 Traffic generator + CronJobs (`k8s/load/traffic.yaml`)

**`traffic-generator` Deployment**
- Image: `python:3.12-alpine`
- Runs the traffic generator script (embedded as ConfigMap) in a loop every 0.8s
- Hits `/healthz`, `GET /posts`, and with 35% probability creates a post, with 25% probability comments on the latest post
- Author name: `k8s-load-bot`

**CronJobs** (3 total):

| Job name | Schedule | What it does |
|---|---|---|
| `task-read-latency` | every 2 min | 60 iterations: hits `/posts?limit=10` + `/healthz` |
| `task-write-throughput` | every 3 min | 30 iterations: `POST /posts` with text content |
| `task-metrics-snapshot` | every 4 min | Pulls `/metrics` and prints first 40 lines to logs |

All CronJobs use `curlimages/curl:8.9.1`.

### 6.10 Kustomization

`k8s/kustomization.yaml` sets `namespace: bartender` and lists all resource files in dependency order. Apply everything with:

```bash
kubectl apply -k k8s/
```

---

## 7. Scripts

### `scripts/minikube_init.sh`

One-command bootstrap. Requires `minikube`, `kubectl`, and `docker` on PATH.

Steps:
1. Checks prerequisites.
2. Starts minikube if not already running.
3. Builds `bartender-backend:local` and `bartender-frontend:local` images into minikube (no registry push needed).
4. Applies `kubectl apply -k k8s/`.
5. Restarts `backend`, `frontend`, and `worker` deployments.
6. Waits (up to 240s each) for: `postgres` StatefulSet, `backend`, `frontend`, `worker`, `prometheus`, `grafana`, `traffic-generator` to roll out.
7. Prints service URLs.

### `scripts/traffic_generator.py`

Local equivalent of the in-cluster load script. Respects `API_BASE` env var (default: `http://backend:8000`). Runs forever in a loop, simulating mixed read/write traffic. Useful for generating Prometheus data during local testing:

```bash
API_BASE=http://$(minikube ip):30001 python scripts/traffic_generator.py
```

---

## 8. Service connectivity map

```
Browser
  └── Frontend (NodePort :30000 → NGINX :80)
        └── serves index.html

index.html (JS in browser)
  └── Backend (NodePort :30001 → Uvicorn :8000)
        ├── PostgreSQL (:5432, ClusterIP internal)
        ├── Redis (:6379, ClusterIP internal)
        │     └── Celery Worker (reads from Redis broker)
        └── /metrics

Prometheus (:30090 → :9090)
  └── scrapes Backend :8000 /metrics every 15s

Grafana (:30300 → :3000)
  └── queries Prometheus http://prometheus:9090

traffic-generator (Deployment)
  └── calls Backend :8000 continuously

CronJobs (3)
  └── call Backend :8000 periodically
```

---

## 9. Observability

### Prometheus metrics (auto-instrumented)

- `http_requests_total` — request count by handler, method, status
- `http_request_duration_seconds` — latency histogram by handler, method

### Custom business metrics

| Metric | Description |
|---|---|
| `bartender_posts_created_total{type}` | Post count per type |
| `bartender_comments_created_total` | Comment count |
| `bartender_auth_logins_total{outcome}` | Login success/failure |
| `bartender_feed_cache_requests_total{outcome}` | Cache hit/miss |
| `bartender_post_create_seconds` | Post write latency histogram |
| `bartender_comment_create_seconds` | Comment write latency histogram |

### OpenTelemetry

- FastAPI auto-instrumented via `FastAPIInstrumentor`.
- Traces exported to OTLP HTTP (default endpoint: `http://localhost:4318`).
- Service name: `bartender-journal-api`.

### Grafana dashboard — "Bartender Journal API Overview"

4 time-series panels; auto-refreshes every 10s; default window is last 15 minutes.

---

## 10. Quick start

### Prerequisites

- `minikube`
- `kubectl`
- `docker`

### Deploy everything

```bash
./scripts/minikube_init.sh
```

### Manual steps (if preferred)

```bash
minikube start
minikube image build -t bartender-backend:local ./backend
minikube image build -t bartender-frontend:local ./frontend
kubectl apply -k k8s/
kubectl -n bartender rollout status statefulset/postgres
kubectl -n bartender rollout status deploy/backend
kubectl -n bartender rollout status deploy/frontend
```

### Access services

```bash
IP=$(minikube ip)
echo "Frontend:   http://$IP:30000"
echo "Backend:    http://$IP:30001"
echo "Prometheus: http://$IP:30090"
echo "Grafana:    http://$IP:30300  (admin/admin)"
```

After opening the frontend, paste the backend URL into the **API** box and click **Save**.

### Quick API smoke test

```bash
IP=$(minikube ip)

# Health
curl "http://$IP:30001/healthz"

# Create a post
curl -X POST "http://$IP:30001/posts" \
  -H "content-type: application/json" \
  -d '{"type":"text","title":"Shift notes","body":"New citrus prep worked great.","author_name":"Guest"}'

# List posts
curl "http://$IP:30001/posts?limit=10"

# Comment on a post (replace POST_ID)
curl -X POST "http://$IP:30001/posts/<POST_ID>/comments" \
  -H "content-type: application/json" \
  -d '{"body":"Nice one.","author_name":"Someone"}'
```

---

## 11. Known limitations / next steps (portfolio ideas)

- **Library**: currently seeded as static hardcoded data in Python. Next step: real DB tables + CRUD + admin.
- **Rate limiting / moderation**: no per-IP limits or spam controls. Redis is already present — a good next step.
- **Image upload**: photo posts accept a URL; no file upload. Could add MinIO/S3 + pre-signed URLs.
- **Celery tasks**: placeholder only. Could wire `process_image` task to be dispatched on photo post creation.
- **Prometheus storage**: `emptyDir` — data is lost on pod restart. Production would use a PVC or remote write.
- **JWT secret**: default is `dev-change-me`. Must be rotated before any real deployment.
- **Grafana credentials**: default `admin/admin`. Must be changed before any real deployment.

---

## 12. Suggested reading order

1. `README.md` — quick start
2. `docs/STAR-summary.md` — resume-style overview
3. `docs/portfolio-feature-walkthrough.md` — interview/demo runbook
4. `backend/app/main.py` — thin entry point (wiring)
5. `backend/app/routes/` — API route handlers
6. `backend/app/models.py` — data model
7. `backend/app/worker.py` — async task architecture
8. `k8s/` manifests — deployment model
9. `k8s/observability/*.yaml` — monitoring and alerting
10. `k8s/load/traffic.yaml` + `scripts/traffic_generator.py` — traffic simulation
