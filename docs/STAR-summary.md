# Bartender Journal — Resume Summary (STAR Format)

## Situation

Needed a production-shaped portfolio project that demonstrates full-stack development and DevOps skills — from async API design through database persistence, caching, background processing, container orchestration, and observability.

## Task

Design and build a community board ("bartender wall") as a complete system:
- Async Python REST API with optional JWT authentication
- PostgreSQL persistence with schema migrations
- Redis caching and Celery background workers
- Kubernetes deployment on minikube (single-command bootstrap)
- Full observability stack: metrics, tracing, dashboards, alerting
- Continuous synthetic traffic to generate realistic dashboard data

## Action

### Backend (FastAPI + Python 3.12)

- Built async REST API with cursor-paginated infinite feed, JWT auth (optional), and comment threads
- Modular codebase: routes, models, schemas, dependencies, metrics, and middleware in separate files
- SQLAlchemy 2.0 async ORM with Alembic migrations (run via Kubernetes init container)
- Redis cache with graceful degradation — feed cached at 5s TTL, library at 60s TTL
- Celery worker on Redis broker for async task processing
- SQLAdmin panel for data management at `/admin`
- 6 custom Prometheus business metrics (post/comment counts, cache hit ratio, write latency histograms)
- OpenTelemetry tracing with OTLP HTTP export

### Frontend

- Single-page vanilla JS app served by NGINX — infinite scroll feed, comments, auth modals, library browser
- XSS-safe rendering with `escapeHtml()` on all user content
- Configurable API base URL saved to localStorage

### Infrastructure (Kubernetes)

- 10+ manifests organized with Kustomize: PostgreSQL StatefulSet (2Gi PVC), Redis, Backend, Frontend, Celery Worker
- ConfigMap/Secret-based configuration; NodePort services for local access
- Health probes (readiness + liveness) on all services
- One-command deploy via `scripts/minikube_init.sh` (builds images, applies manifests, waits for rollouts)

### Observability

- Prometheus scraping backend `/metrics` at 15s intervals
- Pre-provisioned Grafana dashboard: request rate, p95 latency, 5xx errors, traffic by status
- Traffic generator deployment + 3 CronJobs for continuous mixed workload (reads, writes, metrics snapshots)

## Result

- Fully reproducible local deployment in under 5 minutes from a clean minikube
- Live dashboards showing real-time request rates, latencies, cache hit ratios, and error rates
- Clean separation of concerns across ~15 Kubernetes resources and a modular Python backend
- Demonstrates: async Python, SQL + migrations, caching, JWT auth, Kubernetes, Prometheus + Grafana, OpenTelemetry, Docker, CI-ready patterns

## Tech Stack

FastAPI | SQLAlchemy | PostgreSQL | Redis | Celery | Kubernetes | Prometheus | Grafana | OpenTelemetry | Docker | Kustomize | NGINX | Pydantic | Alembic | Argon2
