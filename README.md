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

