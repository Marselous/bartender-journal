# Claude Sessions — Implementation History

## Purpose
Preserves decisions, patterns, and context from each Claude Code session so future
sessions start with full institutional knowledge rather than re-reading all source files
from scratch.

---

## Session Log

### Session 1 — Documentation & Planning (branch: update/plan-overview)

**What was built:**
- `PLAN_OVERVIEW.md` — verified current-state snapshot, 21 backend files catalogued,
  10 confirmed gaps, 3-phase prioritized roadmap
- `PROJECT_REPORT.md` — 31.7 KB HR-facing technical cheat sheet (15 sections)
- `project-visual.html` — 69.5 KB standalone interactive browser visualization:
  SVG architecture diagram, ER diagram, tech stack cards, Grafana mockup,
  API table, security cards, roadmap

**Decisions:**
- Light theme with warm coral accent chosen for visual identity
- Fredoka (display) + DM Sans (body) font pairing locked in

---

### Session 2 — Frontend Redesign Iterations (branches: cl-frontend-type1, type2, init)

**What was built:**
- **Type 1 (dark agency)** — monolithic `index.html`, gold/amber on black, editorial feel
- **Type 2 (light lifestyle)** — introduced Fredoka, coral `#E85A38`, warm neutral palette
- **Final (cl-frontend-init)** — luxury editorial, split into 3 files:
  - `index.html` (~175 lines): structure only
  - `style.css` (~380 lines): full design system with CSS variables
  - `app.js` (~480 lines): all JS logic
  - Key features: glassmorphism plates, `clamp(44px,5.5vw,72px)` hero headline,
    post-type badges, avatar initials with color hash, relative timestamps,
    skeleton loaders, library renders cards (not raw JSON), settings drawer
    behind gear icon, footer

**Security:** `escapeHtml()` / `escapeAttr()` preserved on all user content

---

### Session 3 — Canvas Hero Animation (branch: feature/frontend-animation → merged to config/cl-frontend-init)

**What was built:**
- Animated hero shapes (SVG canvas precursor — later replaced)
- Flickering-grid canvas background:
  - `requestAnimationFrame` loop started eagerly on `DOMContentLoaded`
  - Grid of cells, each flickers probabilistically each frame
  - Opacity bumped so grid is visible
  - `prefers-reduced-motion` guard cancels animation

**Key fix:** Both opacity level *and* eager loop start were needed to make the grid
visible. The loop was starting too late (inside a deferred callback) and opacity was
too low — two separate bugs that together caused a blank canvas.

---

### Session 4 — SVG Favicon (branch: feature/favicon → merged upstream)

**What was built:**
- `frontend/public/favicon.svg` — 32×32 viewBox:
  - Dark navy `#0D1526` rounded-square badge (`rx=7`)
  - Coral `#E85A38` martini glass (wide V polygon + stem rect + base rect)
  - Green `#22C55E` olive garnish (circle on rim)
- `index.html` — replaced `data:,` placeholder with `favicon.svg` + `data:,` fallback

**Merge chain:** `feature/favicon` → `feature/frontend-animation` → `config/cl-frontend-init`

---

### Session 5 — Documentation & Visual Update (branch: documents/visual)

**What was built:**
- `project-visual.html` — added "Frontend Evolution" horizontal timeline section
  showing all 5 UI iterations; marked frontend redesign as DONE in roadmap
- `docs/SESSIONS.md` — this file
- `docs/AGENT_EFFICIENCY.md` — token usage analysis and efficiency tips

---

## Established Patterns (apply in every session)

### Security
- All user content: `escapeHtml()` / `escapeAttr()` before any DOM insertion
- Never raw `innerHTML` with user data

### CSS
- All colors as CSS variables in `:root` — never hardcode hex in rules
- Animate only `transform` and `opacity` — never `transition-all`
- `prefers-reduced-motion` guard on every animation
- `clamp()` for responsive font sizes

### Git
- One feature per session, one `/clear` between unrelated features
- Branch naming: `feature/<name>`, `fix/<name>`, `config/<name>`, `update/<name>`, `documents/<name>`
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Never commit on `master` — PR only

### Backend
- `from __future__ import annotations` in every backend file
- `PostType` enum defined ONCE in `models.py` — `schemas.py` imports it
- Cache keys + TTLs only in `constants.py`

---

## Design Tokens (current)

| Token | Value | Role |
|-------|-------|------|
| `--accent` | `#E85A38` | Coral primary |
| `--dark` | `#0D1526` | Dark navy |
| `--success` | `#22C55E` | Green |
| `--bg` | `#FFFFFF` | Light background |
| `--font-display` | Fredoka | Display headings |
| `--font-body` | DM Sans | Body text |
