## Bartender Journal (minikube self-hosted)

A public “bartender wall” (posts + comments) plus a small library section, designed as a DevOps-friendly portfolio project.

### Tech stack
- **Backend**: FastAPI + SQLAlchemy (async) + Alembic + JWT (optional)
- **DB**: PostgreSQL
- **Frontend**: static landing page (NGINX) with infinite feed + comments UI
- **Orchestration**: Kubernetes via **minikube**

### Repo layout
- `backend/`: FastAPI API + migrations
- `frontend/`: static UI (served by NGINX)
- `k8s/`: minikube manifests (NodePorts)

### Prereqs (local machine)
- `minikube`, `kubectl`, `docker`

### Run on minikube
From `bartender-journal/`:

1) Start minikube

```bash
minikube start
```

2) Build images **into minikube**

```bash
minikube image build -t bartender-backend:local ./backend
minikube image build -t bartender-frontend:local ./frontend
```

3) Deploy everything

```bash
kubectl apply -k k8s/
kubectl -n bartender rollout status statefulset/postgres
kubectl -n bartender rollout status deploy/backend
kubectl -n bartender rollout status deploy/frontend
```

4) Get URLs

```bash
minikube ip
```

- **Frontend**: `http://<MINIKUBE_IP>:30000`
- **Backend**: `http://<MINIKUBE_IP>:30001`

Open the frontend and paste the backend URL into the “API” box, click **Save**, then post to the wall.

### Troubleshooting: "No route to host" when saving API URL

The API URL must be reachable **from the machine where the browser runs**. Same machine as minikube: use `http://$(minikube ip):30001`. Remote/SSH: use the host your browser can reach, or `http://localhost:30001` if you use SSH port-forwarding. Ensure the backend pod is running: `kubectl -n bartender get pods`. After changing the URL, click **Save**; the app pings `/healthz` and shows a clear message.

### Quick API test (curl)
Replace `<IP>` with `minikube ip`.

Health:

```bash
curl "http://<IP>:30001/healthz"
```

Create a public text post:

```bash
curl -X POST "http://<IP>:30001/posts" \
  -H "content-type: application/json" \
  -d '{"type":"text","title":"Shift notes","body":"New citrus prep worked great.","author_name":"Guest"}'
```

List posts:

```bash
curl "http://<IP>:30001/posts?limit=10"
```

Comment on a post (replace `<POST_ID>`):

```bash
curl -X POST "http://<IP>:30001/posts/<POST_ID>/comments" \
  -H "content-type: application/json" \
  -d '{"body":"Love this.","author_name":"Someone"}'
```

### Notes / next upgrades (nice for portfolio)
- Add **rate limiting + spam controls** (Redis, per-IP limits, moderation queue)
- Add **image upload** via MinIO/S3 (pre-signed URLs)
- Turn “library” into real tables + CRUD + admin UI
- Add observability: metrics + traces + dashboards

### Observability stack (Prometheus + Grafana on minikube)
This branch now includes Kubernetes manifests for Prometheus and Grafana:

- **Prometheus** NodePort: `30090`
- **Grafana** NodePort: `30300` (default login `admin/admin`)

Deploy (or update) with:

```bash
kubectl apply -k k8s/
kubectl -n bartender rollout status deploy/prometheus
kubectl -n bartender rollout status deploy/grafana
```

Open services:

```bash
minikube service -n bartender prometheus --url
minikube service -n bartender grafana --url
```

Grafana is pre-provisioned with:
- a Prometheus datasource (`http://prometheus:9090`)
- a starter dashboard: **Bartender Journal API Overview**

#### Step-by-step: access Prometheus and Grafana
1) Confirm pods are healthy:

```bash
kubectl -n bartender get pods -l app=prometheus
kubectl -n bartender get pods -l app=grafana
```

2) Get your minikube IP and open the UIs directly:

```bash
minikube ip
```

- Prometheus: `http://<MINIKUBE_IP>:30090`
- Grafana: `http://<MINIKUBE_IP>:30300`

3) Log in to Grafana:
- username: `admin`
- password: `admin`

4) Open dashboard:
- Navigate to **Dashboards** → **Bartender Journal API Overview**.

5) Verify Prometheus scrape targets:
- Open `http://<MINIKUBE_IP>:30090/targets`
- Ensure `bartender-backend` is `UP`.

6) Verify data in Prometheus expression browser:
- Open `http://<MINIKUBE_IP>:30090/graph`
- Try query: `sum(rate(http_requests_total[1m])) by (handler, method)`

#### Alternative access method (if NodePort is blocked)
Use local port-forwarding:

```bash
kubectl -n bartender port-forward svc/prometheus 9090:9090
kubectl -n bartender port-forward svc/grafana 3000:3000
```

Then open:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

### Useful custom metrics (for real demo results)
These are now exported by the backend at `/metrics`:

- `bartender_posts_created_total{type=...}`: post creation throughput by post type.
- `bartender_comments_created_total`: comment creation throughput.
- `bartender_feed_cache_requests_total{outcome=hit|miss}`: feed cache efficiency.
- `bartender_auth_logins_total{outcome=success|failure}`: login outcome tracking.
- `bartender_post_create_seconds_bucket` and `bartender_comment_create_seconds_bucket`: write-path latency histograms.

Try these in Prometheus **Graph**:

```promql
sum(increase(bartender_posts_created_total[5m])) by (type)
100 * sum(rate(bartender_feed_cache_requests_total{outcome="hit"}[5m])) / clamp_min(sum(rate(bartender_feed_cache_requests_total[5m])), 0.01)
histogram_quantile(0.95, sum(rate(bartender_post_create_seconds_bucket[5m])) by (le))
```

### Alerts configured in Prometheus
Prometheus now evaluates alert rules and shows them in **Alerts** page (`/alerts`).

Configured alerts:
- `BartenderBackendDown` (critical)
- `BartenderHigh5xxErrorRate` (warning)
- `BartenderHighP95Latency` (warning)
- `BartenderLowFeedCacheHitRatio` (info)
- `BartenderNoPostCreation` (info)

Open alerts UI:
- `http://<MINIKUBE_IP>:30090/alerts`

In Grafana, dashboard includes **Active Prometheus Alerts** stat panel so you can quickly see firing alerts during tests.

#### Quick troubleshooting
- No dashboard data yet? Generate traffic and wait 1-2 minutes for scrape intervals:

```bash
kubectl -n bartender logs deploy/traffic-generator --tail=100
kubectl -n bartender get cronjobs
```

- Prometheus target is DOWN?

```bash
kubectl -n bartender logs deploy/prometheus --tail=100
kubectl -n bartender get svc backend
```

- Grafana cannot query Prometheus?

```bash
kubectl -n bartender logs deploy/grafana --tail=100
```

### Data collection tasks (3 scheduled tasks)
Three `CronJob` tasks are included to continuously generate dataset samples for dashboards:

1. `task-read-latency` (every 2 min): hits `/posts` and `/healthz` repeatedly.
2. `task-write-throughput` (every 3 min): sends repeated `POST /posts` requests.
3. `task-metrics-snapshot` (every 4 min): pulls `/metrics` sample lines.

Useful commands:

```bash
kubectl -n bartender get cronjobs
kubectl -n bartender get jobs --sort-by=.metadata.creationTimestamp
kubectl -n bartender logs job/<latest-job-name>
```

### Continuous traffic generator
A dedicated deployment (`traffic-generator`) emulates mixed production workflow:
- reads hot endpoints (`/healthz`, `/posts`)
- creates posts (`text/link/photo`)
- adds comments on newest posts

Check status/logs:

```bash
kubectl -n bartender rollout status deploy/traffic-generator
kubectl -n bartender logs deploy/traffic-generator --tail=100
```

You can also run the same logic locally with:

```bash
python scripts/traffic_generator.py
```
(override base URL with `API_BASE=http://<MINIKUBE_IP>:30001`).
