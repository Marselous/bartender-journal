# Bartender Journal — Feature Walkthrough & Demo Runbook

This guide is designed for:
- **you** (project owner) to present the system confidently,
- **reviewers/interviewers** to quickly understand the architecture,
- **contributors** to run and validate each feature.

---

## 1) Quick navigation

- [2) Architecture map](#2-architecture-map)
- [3) Environment setup](#3-environment-setup)
- [4) Core app features](#4-core-app-features)
- [5) Redis cache feature](#5-redis-cache-feature)
- [6) Worker (Celery) feature](#6-worker-celery-feature)
- [7) Admin panel feature](#7-admin-panel-feature)
- [8) Observability feature](#8-observability-feature)
- [9) Synthetic traffic + scheduled tasks](#9-synthetic-traffic--scheduled-tasks)
- [10) End-to-end demo script (portfolio presentation)](#10-end-to-end-demo-script-portfolio-presentation)
- [11) Troubleshooting index](#11-troubleshooting-index)

---

## 2) Architecture map

### 2.1 Runtime components

1. **Frontend** (NGINX static site)
   - Public entrypoint for UI.
2. **Backend API** (FastAPI)
   - Auth, posts, comments, library endpoints.
3. **PostgreSQL**
   - Persistent relational data (users/posts/comments).
4. **Redis**
   - Cache + Celery broker/backend.
5. **Worker** (Celery)
   - Async/background processing tasks.
6. **Prometheus**
   - Scrapes `/metrics`, evaluates alert rules.
7. **Grafana**
   - Dashboards with Prometheus datasource.
8. **Traffic generator + CronJobs**
   - Produce continuous load/data points.

### 2.2 Request/data flow (simple)

- User opens UI → frontend calls backend APIs.
- Backend reads/writes Postgres.
- Backend caches hot `/posts` reads in Redis.
- Backend exposes metrics at `/metrics`.
- Prometheus scrapes metrics + computes alerts.
- Grafana visualizes metrics and alert state.
- Traffic generator/CronJobs create load so charts are non-empty.

---

## 3) Environment setup

### 3.1 Prerequisites

- `minikube`
- `kubectl`
- `docker`

### 3.2 Build and deploy

```bash
minikube start
minikube image build -t bartender-backend:local ./backend
minikube image build -t bartender-frontend:local ./frontend
kubectl apply -k k8s/
```

### 3.3 Confirm rollout

```bash
kubectl -n bartender rollout status statefulset/postgres
kubectl -n bartender rollout status deploy/backend
kubectl -n bartender rollout status deploy/frontend
kubectl -n bartender rollout status deploy/worker
kubectl -n bartender rollout status deploy/prometheus
kubectl -n bartender rollout status deploy/grafana
kubectl -n bartender rollout status deploy/traffic-generator
```

---

## 4) Core app features

### 4.1 What the core API does

- Health check (`/healthz`).
- Register/login (JWT).
- Create/list posts.
- Create/list comments.
- Library sample endpoints.

### 4.2 Code entrypoints

- API routes: `backend/app/main.py`
- Models: `backend/app/models.py`
- Schemas: `backend/app/schemas.py`
- Security: `backend/app/security.py`

### 4.3 Simple tests (manual)

```bash
IP=$(minikube ip)
curl "http://$IP:30001/healthz"
curl "http://$IP:30001/posts?limit=5"
```

Create a post:

```bash
curl -X POST "http://$IP:30001/posts" \
  -H "content-type: application/json" \
  -d '{"type":"text","title":"Portfolio test","body":"Hello from walkthrough","author_name":"demo"}'
```

---

## 5) Redis cache feature

### 5.1 What it does

The hot feed endpoint (`GET /posts`) uses Redis as a short-lived cache. On repeated requests with same limit/cursor:
- cache **hit** = returns fast from Redis,
- cache **miss** = queries DB, then stores result.

### 5.2 Where in code

- Cache helpers: `backend/app/cache.py`
- Cache usage in feed endpoint: `backend/app/main.py` (`list_posts`)
- Redis config: `backend/app/settings.py`, `k8s/backend.yaml`, `k8s/redis.yaml`

### 5.3 How to test quickly

1) Warm cache:
```bash
curl "http://$IP:30001/posts?limit=10" >/dev/null
```

2) Hit again (should be cached path):
```bash
curl "http://$IP:30001/posts?limit=10" >/dev/null
```

3) Verify metrics reflect cache behavior:
```bash
curl -s "http://$IP:30001/metrics" | grep bartender_feed_cache_requests_total
```

---

## 6) Worker (Celery) feature

### 6.1 What it does

Background task service for asynchronous operations.
Current tasks are placeholders useful for architecture demonstration:
- `tasks.process_image`
- `tasks.send_notification`

### 6.2 Where in code

- Celery app + tasks: `backend/app/worker.py`
- Worker deployment: `k8s/worker.yaml`

### 6.3 How to test quickly

Check worker logs to verify service is up and consuming:

```bash
kubectl -n bartender logs deploy/worker --tail=100
```

(Optional) open backend shell/pod and enqueue a task using Celery app if you want a live demo.

---

## 7) Admin panel feature

### 7.1 What it does

Provides CRUD-style management UI for:
- users,
- posts,
- comments.

### 7.2 Where in code

- SQLAdmin setup + model views in `backend/app/main.py` (`UserAdmin`, `PostAdmin`, `CommentAdmin`).

### 7.3 How to test quickly

Open backend URL and navigate to admin route:

```bash
echo "http://$(minikube ip):30001/admin"
```

Verify that tables appear and list data created via API/UI.

---

## 8) Observability feature

### 8.1 What it does

- Prometheus scrapes backend metrics.
- Prometheus evaluates alert rules.
- Grafana shows metrics + active alerts panel.

### 8.2 Where in code/manifests

- App metrics instrumentation: `backend/app/main.py`
- Prometheus scrape + alert config: `k8s/observability/prometheus.yaml`
- Grafana datasource/dashboard provisioning: `k8s/observability/grafana.yaml`

### 8.3 Access URLs

```bash
IP=$(minikube ip)
echo "Prometheus: http://$IP:30090"
echo "Grafana:    http://$IP:30300"
```

Grafana default login: `admin / admin`

### 8.4 Useful queries to show in demo

```promql
sum(rate(http_requests_total{job="bartender-backend"}[1m])) by (handler, method)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="bartender-backend"}[5m])) by (le))
100 * sum(rate(http_requests_total{job="bartender-backend",status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total{job="bartender-backend"}[5m])), 0.01)
sum(increase(bartender_posts_created_total[5m])) by (type)
100 * sum(rate(bartender_feed_cache_requests_total{outcome="hit"}[5m])) / clamp_min(sum(rate(bartender_feed_cache_requests_total[5m])), 0.01)
```

### 8.5 Alerts configured

- `BartenderBackendDown`
- `BartenderHigh5xxErrorRate`
- `BartenderHighP95Latency`
- `BartenderLowFeedCacheHitRatio`
- `BartenderNoPostCreation`

Check alerts page:

```bash
echo "http://$(minikube ip):30090/alerts"
```

---

## 9) Synthetic traffic + scheduled tasks

### 9.1 What it does

- `traffic-generator` deployment continuously emulates real traffic.
- CronJobs periodically stress read/write/metrics endpoints.

### 9.2 Where in manifests/scripts

- In-cluster load setup: `k8s/load/traffic.yaml`
- Local equivalent load script: `scripts/traffic_generator.py`

### 9.3 How to run/verify

```bash
kubectl -n bartender get deploy traffic-generator
kubectl -n bartender logs deploy/traffic-generator --tail=100
kubectl -n bartender get cronjobs
kubectl -n bartender get jobs --sort-by=.metadata.creationTimestamp
```

Run local load (optional):

```bash
API_BASE="http://$(minikube ip):30001" python scripts/traffic_generator.py
```

---

## 10) End-to-end demo script (portfolio presentation)

Use this flow in interviews/reviews:

1. Show architecture (components + flow from section 2).
2. Deploy app (`kubectl apply -k k8s/`).
3. Prove app works (`/healthz`, create post, add comment).
4. Open Grafana dashboard and Prometheus targets.
5. Start/confirm traffic generator and CronJobs.
6. Watch metrics move live:
   - request rate,
   - post/comment throughput,
   - cache hit ratio,
   - p95 latency.
7. Show alert page and explain thresholds.
8. Summarize DevOps value:
   - observability,
   - async worker,
   - caching,
   - reproducible k8s deployment.

---

## 11) Troubleshooting index

### Pods not ready

```bash
kubectl -n bartender get pods
kubectl -n bartender describe pod <pod-name>
kubectl -n bartender logs <pod-name> --all-containers
```

### Prometheus target is DOWN

```bash
kubectl -n bartender logs deploy/prometheus --tail=100
kubectl -n bartender get svc backend
kubectl -n bartender get endpoints backend
```

### Grafana dashboard empty

- Wait 1-2 minutes for scrapes.
- Confirm traffic generator is running.
- Confirm Prometheus query returns data before checking Grafana panel.

### No backend metrics

```bash
curl -s "http://$(minikube ip):30001/metrics" | head -n 40
```

---

## 12) Suggested reading order (for newcomers)

1. `README.md` (quick start)
2. `docs/portfolio-feature-walkthrough.md` (this guide)
3. `backend/app/main.py` (API + instrumentation)
4. `backend/app/worker.py` (async processing)
5. `k8s/` manifests (deployment model)
6. `k8s/observability/*.yaml` (monitoring/alerts)
7. `k8s/load/traffic.yaml` + `scripts/traffic_generator.py` (traffic simulation)
