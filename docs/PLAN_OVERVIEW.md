# Bartender Journal — Plan Overview

> **Purpose**: Current-state snapshot verified against source code (branch `update/plan-overview`, HEAD `829a3ba`).
> Informs prioritization of future work. See `ARCHITECTURE.md` for the full technical reference.

---

## 1. What is this project?

A full-stack DevOps portfolio project — a "bartender wall" community board where users post shift notes, links, and photos, comment on content, and browse a cocktail library. Designed to demonstrate production-like patterns deployable with a single command on minikube.

---

## 2. Verified current state

Everything below was confirmed by reading source files directly.

### 2.1 Backend (`backend/app/`)

| File | Role | Status |
|------|------|--------|
| `main.py` | Wires routers, CORS, OTel, Prometheus, admin | Done |
| `routes/health.py` | `GET /healthz` → `{ok, ts}` | Done |
| `routes/auth.py` | `POST /auth/register`, `POST /auth/login` | Done |
| `routes/posts.py` | `GET /posts` (cursor paged), `POST /posts` | Done |
| `routes/comments.py` | `GET /posts/{id}/comments`, `POST /posts/{id}/comments` | Done |
| `routes/library.py` | `GET /library/recipes,places,history` | Done — hardcoded seed only |
| `models.py` | User, Post, Comment ORM + PostType enum | Done |
| `schemas.py` | Pydantic v2 DTOs — imports PostType from models | Done |
| `db.py` | Async SQLAlchemy engine + session factory | Done |
| `cache.py` | Redis wrapper, graceful degradation on any RedisError | Done |
| `security.py` | Argon2 hashing, JWT HS256 create/decode | Done |
| `settings.py` | pydantic-settings, env/`.env`, CORS origins parsing | Done |
| `constants.py` | Cache keys, TTLs, app defaults | Done |
| `dependencies.py` | `get_optional_user` — silent fail on bad/missing token | Done |
| `helpers.py` | `now_utc()`, `resolve_author_name()` | Done |
| `middleware.py` | Adds `x-app: bartender-journal` header | Done |
| `metrics.py` | 4 Counters + 2 Histograms (Prometheus) | Done |
| `pagination.py` | base64url cursor encode/decode (created_at + id) | Done |
| `admin.py` | SQLAdmin views for User, Post, Comment (no auth) | Done |
| `worker.py` | Celery app + 2 placeholder tasks — never dispatched | Skeleton only |
| `run_migrations.py` | Alembic runner invoked by k8s init container | Done |

### 2.2 Data model

```
User       id(UUID PK) | email(uniq) | username(uniq) | password_hash | created_at
Post       id(UUID PK) | created_at(idx) | type(enum) | title | body | link_url | image_url | author_id(FK nullable) | author_name
Comment    id(UUID PK) | post_id(FK CASCADE) | created_at(idx) | body | author_id(FK nullable) | author_name
```

PostType enum: `text | link | photo` — defined once in `models.py`, imported by `schemas.py`.

### 2.3 Auth model

- JWT HS256, 24h expiry, secret from `JWT_SECRET_KEY` env var (default: `dev-change-me`).
- Every write endpoint accepts either a valid Bearer token or no token at all.
- With token: `author_id` = user UUID, `author_name` = username from DB.
- Without token: `author_id` = null, `author_name` = provided value or `"Guest"`.

### 2.4 Caching

| Endpoint | Cache key pattern | TTL |
|----------|------------------|-----|
| `GET /posts` | `posts:limit={n}:cursor={c}` | 5 s |
| `GET /library/*` | `library:recipes`, `library:places`, `library:history` | 60 s |

Redis unavailable → all cache ops silently become misses. App continues normally.

### 2.5 Infrastructure (`k8s/`)

| Manifest | Resource | NodePort |
|----------|----------|----------|
| `namespace.yaml` | Namespace `bartender` | — |
| `postgres.yaml` | StatefulSet + 2Gi PVC + ClusterIP :5432 | — |
| `redis.yaml` | Deployment + ClusterIP :6379 | — |
| `backend.yaml` | Deployment (init: migrations) + ConfigMap + Secret + Service | 30001 |
| `frontend.yaml` | NGINX Deployment + Service | 30000 |
| `worker.yaml` | Celery worker Deployment | — |
| `observability/prometheus.yaml` | Prometheus v2.55.1, scrapes `/metrics` every 15s, emptyDir | 30090 |
| `observability/grafana.yaml` | Grafana 11.2.2, pre-provisioned dashboard | 30300 |
| `load/traffic.yaml` | traffic-generator Deployment + 3 CronJobs | — |

All resources applied via single `kubectl apply -k k8s/`.

### 2.6 Load / traffic generation

- **Deployment** `traffic-generator`: continuous loop at 0.8s interval — health check, feed reads, 35% chance create post, 25% chance comment on latest post.
- **CronJob** `task-read-latency`: every 2 min — 60× GET /posts + GET /healthz.
- **CronJob** `task-write-throughput`: every 3 min — 30× POST /posts.
- **CronJob** `task-metrics-snapshot`: every 4 min — GET /metrics, head -40.

### 2.7 Observability

- Prometheus scrape: `backend:8000/metrics` + `backend:8000/healthz` every 15s.
- Grafana: request rate, p95 latency, 5xx error rate, traffic by status — pre-provisioned on boot.
- OTel: `BatchSpanProcessor` → `OTLPSpanExporter` (default OTLP HTTP endpoint; no collector configured in k8s yet).
- Prometheus storage: `emptyDir` — metrics lost on pod restart.

### 2.8 Frontend

- Single file `frontend/public/index.html` (~680 lines), vanilla JS, zero build tooling.
- Sections: sticky nav, hero/about (configurable API base URL), new post form, library panel, infinite scroll feed with inline comment threads, auth modals (register/login), toast notifications.
- XSS protection: `escapeHtml()` applied to all user content before DOM insertion.
- JWT stored in `localStorage`; sent as `Authorization: Bearer` header.

---

## 3. Known gaps (verified)

| # | Gap | Location | Notes |
|---|-----|----------|-------|
| 1 | Library is hardcoded seed data | `routes/library.py` | No DB tables; `Recipe`, `Place`, `HistoryEntry` schemas exist but are never persisted |
| 2 | Celery tasks never dispatched | `worker.py`, `routes/posts.py` | `process_image` and `send_notification` tasks defined but no `.delay()` calls anywhere |
| 3 | JWT secret hardcoded in k8s Secret | `k8s/backend.yaml:19` | `"dev-change-me-in-k8s"` — needs rotation before any real deployment |
| 4 | No rate limiting | All write routes | Redis is already available; could use `redis-py` sliding window or `slowapi` |
| 5 | Image upload is URL-only | `schemas.py:PostCreateRequest` | `image_url` is `HttpUrl | None`; no file upload, no object storage |
| 6 | Prometheus storage is ephemeral | `k8s/observability/prometheus.yaml:62` | `emptyDir` — all historical data lost on pod restart |
| 7 | No OTel collector in k8s | `main.py:28` | `OTLPSpanExporter` uses default endpoint; no collector/Jaeger/Tempo deployed |
| 8 | Admin panel has no auth | `admin.py:29-34` | `Admin(app, engine)` with no `authentication_backend` |
| 9 | No test suite | — | Manual curl verification only; no pytest, no fixtures |
| 10 | Frontend design not updated | `docs/landing-page-research-context.md` | Research complete, redesign not yet implemented |

---

## 4. Prioritized next steps

The following order balances portfolio visibility (items that show up in a live demo) with correctness.

### P1 — High portfolio impact

1. **Dispatch Celery tasks from API** — Call `process_image.delay(post_id, image_url)` on photo post creation. Demonstrates the full async task pipeline is live, not just defined.
2. **Persist library data in DB** — Add `Recipe`, `Place`, `HistoryEntry` tables, a migration, and CRUD routes. Closes the most obvious gap in the data model.
3. **Frontend redesign** — Apply the research in `docs/landing-page-research-context.md`. First impression matters for a portfolio project.

### P2 — Correctness / realism

4. **Rate limiting** — Add `slowapi` (wraps Redis) on POST endpoints. Realistic production concern, easy to add.
5. **Prometheus PVC** — Replace `emptyDir` with a `PersistentVolumeClaim` so metrics survive pod restarts. Shows infrastructure awareness.
6. **OTel collector** — Deploy OpenTelemetry Collector (or Jaeger all-in-one) to actually receive and display traces.

### P3 — Quality / hardening

7. **Test suite** — Add `pytest-asyncio` + `httpx.AsyncClient` for at least the happy-path routes.
8. **Admin auth** — Add `sqladmin.authentication.AuthenticationBackend` with a dev password.
9. **JWT secret rotation** — Document and script secret rotation for k8s Secret `backend-secret`.

---

## 5. One-command deploy reference

```bash
./scripts/minikube_init.sh
# Requires: minikube, kubectl, docker
# Builds bartender-backend:local and bartender-frontend:local into minikube
# Applies kubectl apply -k k8s/
# Waits for all rollouts
# Prints URLs

minikube ip   # then:
# Frontend:   http://<IP>:30000
# API:        http://<IP>:30001
# Prometheus: http://<IP>:30090
# Grafana:    http://<IP>:30300  (admin / admin)
```

Quick API smoke test:
```bash
IP=$(minikube ip)
curl http://${IP}:30001/healthz
curl http://${IP}:30001/posts
curl http://${IP}:30001/library/recipes
```
