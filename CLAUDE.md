# CLAUDE.md — Project Context for AI Assistants

## Project
Bartender Journal — a full-stack DevOps portfolio project. A "bartender wall" community board where users post shift notes, links, and photos, comment, and browse a cocktail library.

## Always do first (frontend sessions)
- **Invoke the `frontend-design` skill** before writing any frontend code, every session, no exceptions.
- Check `brand_assets/` for logos, color guides, or style references before designing anything.

## Key paths
- Backend API: `backend/app/` (FastAPI, Python 3.12)
- Routes: `backend/app/routes/` (health, auth, posts, comments, library)
- Models: `backend/app/models.py` (SQLAlchemy async)
- Schemas: `backend/app/schemas.py` (Pydantic v2)
- Frontend: `frontend/public/` (index.html, style.css, app.js)
- Brand assets: `brand_assets/` (logos, color guides — use these, never invent brand colors)
- K8s manifests: `k8s/` (Kustomize root)
- See @docs/ARCHITECTURE.md for full architecture reference

## Commands
```bash
# Local k8s deploy (one command)
./scripts/minikube_init.sh

# Frontend dev server — always use this, never open file:/// directly
node serve.mjs   # serves frontend/public/ at http://localhost:3000

# Backend dev server (outside k8s)
cd backend && uvicorn app.main:app --reload --port 8000

# Lint / format
cd backend && ruff check . && ruff format .

# DB migrations
cd backend && alembic upgrade head
```

## Screenshot loop workflow
- **Always serve on localhost** before screenshotting — never use a `file:///` URL.
- Start the dev server in the background: `node serve.mjs`
- If the server is already running, do not start a second instance.
- Take screenshots with: `node screenshot.mjs http://localhost:3000`
- Screenshots save to `./temporary-screenshots/screenshot-N.png` (auto-incremented, never overwritten).
- Optional label: `node screenshot.mjs http://localhost:3000 hero` → `screenshot-N-hero.png`
- After screenshotting, read the PNG with the Read tool — analyze the image directly.

**Iteration rules:**
1. Make the change
2. Screenshot → read the PNG → analyze visually
3. Be specific when comparing: "heading is 32px but reference shows ~24px", "card gap is 16px but should be 24px"
4. Fix mismatches → re-screenshot. Minimum 2 rounds. Stop only when no visible differences remain or user says so.
5. Check each round: spacing/padding, font size/weight/line-height, colors (exact hex), alignment, border-radius, shadows, image sizing.

If a component is heavily animated, disable the loop and review manually.

## Reference image rules
- If a reference image is provided: match layout, spacing, typography, and color exactly. Use placeholder content (`https://placehold.co/WIDTHxHEIGHT`). Do not improve or add to the design.
- If no reference image: design from scratch using the guardrails below.

## Frontend conventions
- Stack: vanilla HTML/CSS/JS — no build step, no framework
- Files: `frontend/public/index.html` (structure), `style.css` (design), `app.js` (logic)
- Design system: dark glassmorphism — all colors as CSS variables in `:root`, never hardcode
- Security: ALWAYS use `escapeHtml()` / `escapeAttr()` for user content — never raw `innerHTML`
- Mobile-first CSS; use `clamp()` for responsive font sizes
- NEVER use Lorem Ipsum or placeholder images in production output

## Frontend aesthetics (avoid "AI slop")
- **Colors:** Never invent brand colors — use `brand_assets/` or derive from the established palette. Never default to generic indigo/blue.
- **Shadows:** Never flat `shadow-md`. Use layered, color-tinted shadows with low opacity.
- **Typography:** Never the same font for headings and body. Pair a display/serif with a clean sans (Space Grotesk + JetBrains Mono). Tight tracking (`-0.03em`) on large headings, generous line-height (`1.7`) on body. Weight contrast: 100–200 vs 800–900, not 400 vs 600.
- **Gradients:** Layer multiple radial gradients. Add grain/texture via SVG noise filter for depth.
- **Animations:** Only animate `transform` and `opacity`. Never `transition-all`. Use spring-style easing. Always include `prefers-reduced-motion` guard.
- **Interactive states:** Every clickable element needs hover, `focus-visible`, and active states. No exceptions.
- **Images:** Add a gradient overlay (`background: linear-gradient(to top, rgba(0,0,0,0.6), transparent)`) and a color treatment layer.
- **Spacing:** Consistent spacing tokens — not random steps.
- **Depth:** Surfaces have a layering system (base → elevated → floating), not all on the same z-plane.
- **Layouts:** Asymmetric and intentional — avoid cookie-cutter card grids.

## Git branching workflow
- NEVER work directly on `master`
- Branch naming: `feature/<name>`, `fix/<name>`, `config/<name>`, `update/<name>`
- One feature per chat session; use `/clear` when switching context
- Commit format: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
- Each commit must leave the app in a working state
- Do NOT reference AI tools in commit messages
- Review diffs before pushing; get confirmation before pushing to `master`
- For parallel work: `git worktree add ../bj-<feature> -b <branch>`

## Backend conventions
- All backend files use `from __future__ import annotations`
- `PostType` enum defined ONCE in `models.py`; `schemas.py` imports it — never redefine it
- Cache keys and TTLs live in `constants.py`
- Route files use `FastAPI APIRouter`; `main.py` is a thin wiring file only
- Kubernetes namespace: `bartender`
- NEVER commit `.env` files or secrets

## Hard rules
- Do not add sections, features, or content not in the reference
- Do not "improve" a reference design — match it exactly
- Do not stop after one screenshot pass
- Do not use `transition-all`
- Do not use `innerHTML` with user content — use `escapeHtml()` always
- Do not redefine `PostType` — it lives in `models.py`
- Do not add inline styles when CSS variables exist
- Do not add docstrings or type annotations to code you didn't change
- Do not guess NodePort URLs — check with `minikube ip` at runtime

## Testing
No automated test suite yet. Manual verification via curl (see README.md).

## NodePort URLs (after `minikube start`)
- Frontend: `http://<minikube-ip>:30000`
- API: `http://<minikube-ip>:30001`
- Prometheus: `http://<minikube-ip>:30090`
- Grafana: `http://<minikube-ip>:30300` (admin/admin)
