# CLAUDE.md — Project Context for AI Assistants

## Project
Bartender Journal — a full-stack DevOps portfolio project. A "bartender wall" community board where users post shift notes, links, and photos, comment, and browse a cocktail library.

## Key paths
- Backend API: `backend/app/` (FastAPI, Python 3.12)
- Routes: `backend/app/routes/` (health, auth, posts, comments, library)
- Models: `backend/app/models.py` (SQLAlchemy async)
- Schemas: `backend/app/schemas.py` (Pydantic v2)
- Frontend: `frontend/public/` (index.html, style.css, app.js)
- K8s manifests: `k8s/` (Kustomize root)
- Docs: `docs/ARCHITECTURE.md` (full reference), `docs/STAR-summary.md` (resume)
- See @docs/ARCHITECTURE.md for full architecture reference

## Commands
```bash
# Local k8s deploy (one command)
./scripts/minikube_init.sh

# Frontend dev (static files, no build step)
open frontend/public/index.html

# Backend dev server (outside k8s)
cd backend && uvicorn app.main:app --reload --port 8000

# Lint / format
cd backend && ruff check . && ruff format .

# DB migrations
cd backend && alembic upgrade head
```

## Backend conventions
- All backend files use `from __future__ import annotations`
- `PostType` enum defined ONCE in `models.py`; `schemas.py` imports it — never redefine it
- Cache keys and TTLs live in `constants.py`
- Route files use `FastAPI APIRouter`; `main.py` is a thin wiring file only
- Kubernetes namespace: `bartender`
- NEVER commit `.env` files or secrets

## Frontend conventions
- Stack: vanilla HTML/CSS/JS — no build step, no framework
- Files: `frontend/public/index.html` (structure), `style.css` (design), `app.js` (logic)
- Design: dark glassmorphism — CSS variables in `:root`, never hardcode colors
- Security: ALWAYS use `escapeHtml()` / `escapeAttr()` for user content — never raw `innerHTML`
- NEVER use Lorem Ipsum or placeholder images in the final output
- NEVER use generic system fonts (Arial, Roboto) — use Space Grotesk or JetBrains Mono
- Mobile-first CSS; use `clamp()` for responsive font sizes

## Frontend aesthetics (avoid "AI slop")
- Weight contrast: 100–200 vs 800–900, not 400 vs 600
- Color: dominant dark + one sharp accent, controlled via CSS variables
- Motion: CSS-only animations; always include `prefers-reduced-motion` guard
- Backgrounds: layered gradients or subtle geometric patterns, not solid colors
- Layouts: asymmetric, intentional — avoid cookie-cutter card grids

## Screenshot loop workflow
When building or iterating on the frontend:
1. Make the change
2. Take a screenshot of the result in the browser
3. Paste the screenshot into the chat for visual review
4. Iterate based on what you see — do not describe visual problems in text if you can show them
5. Repeat until the output matches the intent (typically 2–3 rounds)

If a component is heavily animated, disable the loop and review manually.

## Git branching workflow
- NEVER work directly on `master`
- Branch naming: `feature/<name>`, `fix/<name>`, `config/<name>`, `update/<name>`
- One feature per chat session; use `/clear` when switching context
- Commit format: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
- Each commit must leave the app in a working state
- Do NOT reference AI tools in commit messages
- Review diffs before pushing; get confirmation before pushing to `master`
- For parallel work, use git worktrees: `git worktree add ../bj-<feature> -b <branch>`

## What NOT to do
- Do not redefine `PostType` — it lives in `models.py`
- Do not add inline styles when CSS variables exist
- Do not add docstrings or type annotations to code you didn't change
- Do not create helper utilities for one-off operations
- Do not add backwards-compatibility shims unless explicitly asked
- Do not use `innerHTML` with user content — use `escapeHtml()` always
- Do not guess NodePort URLs — check with `minikube ip` at runtime

## Testing
No automated test suite yet. Manual verification via curl (see README.md).

## NodePort URLs (after `minikube start`)
- Frontend: `http://<minikube-ip>:30000`
- API: `http://<minikube-ip>:30001`
- Prometheus: `http://<minikube-ip>:30090`
- Grafana: `http://<minikube-ip>:30300` (admin/admin)
