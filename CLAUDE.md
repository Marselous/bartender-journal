# CLAUDE.md — Project Context for AI Assistants

## Project
Bartender Journal — a full-stack DevOps portfolio project.

## Key paths
- Backend API: `backend/app/` (FastAPI, Python 3.12)
- Routes: `backend/app/routes/` (health, auth, posts, comments, library)
- Models: `backend/app/models.py` (SQLAlchemy async)
- Schemas: `backend/app/schemas.py` (Pydantic v2)
- K8s manifests: `k8s/` (Kustomize root)
- Docs: `docs/ARCHITECTURE.md` (full reference), `docs/STAR-summary.md` (resume)

## Conventions
- All backend code uses `from __future__ import annotations`
- PostType enum is defined ONCE in `models.py`; schemas.py imports it
- Cache keys and TTLs live in `constants.py`
- Route files use FastAPI APIRouter; main.py is a thin wiring file
- Kubernetes namespace: `bartender`

## Running locally
```bash
./scripts/minikube_init.sh
```

## Testing
No test suite yet. Manual verification via curl (see README.md).
