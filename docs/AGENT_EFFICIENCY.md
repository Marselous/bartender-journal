# Claude Code Agent Efficiency Guide

## Context Usage Summary (this project)

| Metric | Value |
|--------|-------|
| Major sessions run | 5 |
| Total documents generated | ~170 KB of HTML/Markdown |
| Fixed overhead per session (CLAUDE.md + ARCHITECTURE.md) | ~35 KB (~9,000 tokens) |

**Largest single-session context consumers:**
- `landing-page-research-context.md` — 7 live browser fetches + 17.9 KB output
- `project-visual.html` generation — 69.5 KB output file
- Multi-file frontend redesigns — reading 3 files × 400+ lines each

**Estimated token ranges per session type:**

| Session type | Estimated tokens |
|-------------|-----------------|
| Documentation / planning session | 60,000–100,000 |
| Frontend redesign with screenshots | 80,000–150,000 |
| Small targeted fix (favicon, single component) | 20,000–50,000 |

---

## Why Sessions Get Slow

1. **Fixed CLAUDE.md overhead** — loaded every message (~35 KB)
2. **Reading entire large files** when only a section is needed
3. **Screenshot loops** — each PNG image read adds 50–500 KB of vision tokens
4. **Subagent chains** — Explore + Plan agents each consume their own context budget
5. **Broad Bash searches** (`find`, `grep -r`) instead of dedicated Glob/Grep tools
6. **Re-reading files after editing** — not necessary; edit confirmation is enough

---

## Speed & Efficiency Tips

### High Impact

| Tip | Why it helps |
|-----|-------------|
| `/clear` between unrelated features | Fully resets context; start fresh each session |
| Use Grep instead of Explore agent for known symbols | 10× faster for targeted searches |
| Reference `file:line` when asking about specific code | Agent reads less |
| Keep CLAUDE.md under 150 lines | Loaded every message — smaller = cheaper |

### Medium Impact

| Tip | Why it helps |
|-----|-------------|
| Use `limit`/`offset` on Read tool for large files | Read only the section you need |
| Use `head_limit` on Grep to cap results | Prevents 200-line search dumps |
| Skip screenshot loop for non-visual changes | Each PNG read = significant tokens |
| Specify exact file paths in your prompt | Avoids exploratory file searches |

### Low Impact

| Tip | Why it helps |
|-----|-------------|
| Use `git diff HEAD~1` to review changes | Faster than re-reading whole files |
| Don't re-read files right after writing them | The Write/Edit confirmation is enough |
| Avoid `transition-all` in CSS | Keeps style.css smaller over time |

---

## CLAUDE.md Optimization

Current `CLAUDE.md` is ~230 lines — loaded as context overhead every session.
Candidate sections to extract to permanent docs:

| Section | Extract to |
|---------|-----------|
| Brand palette + fonts | `docs/DESIGN_TOKENS.md` |
| Full git workflow rules | `docs/GIT_WORKFLOW.md` (reference from CLAUDE.md) |
| Backend conventions | Already in `ARCHITECTURE.md` — remove duplicate |

**Target:** CLAUDE.md under 100 lines covering only the "always do first" rules,
key paths, commands, and hard rules. Everything else in referenced docs.

---

## Model Selection

| Model | Use case |
|-------|----------|
| `claude-sonnet-4-6` (current) | Default for all coding tasks |
| `claude-opus-4-6` | Complex architectural planning, multi-file refactors |
| `claude-haiku-4-5` | Mechanical edits: rename, reformat, simple copy changes |

Switch model with `/model` in Claude Code CLI.

---

## Session Template (copy-paste starter)

When starting a new session on this project:

1. State the branch you are on or creating
2. State the single feature/fix in scope
3. Reference the specific files involved (from `SESSIONS.md` or `ARCHITECTURE.md`)
4. Avoid "look at everything and tell me what to do" — be specific

**Example good session start:**

```
On branch config/cl-frontend-init. Add a rate-limit banner to the new-post form
in frontend/public/app.js — show a toast if POST /posts returns 429.
No backend changes needed.
```

---

## File Size Reference (key files)

| File | Lines | Notes |
|------|-------|-------|
| `docs/project-visual.html` | ~1200 | Full read = expensive; use offset/limit |
| `docs/ARCHITECTURE.md` | 535 | Comprehensive; read only relevant section |
| `frontend/public/app.js` | ~480 | Read whole file for JS changes |
| `frontend/public/style.css` | ~380 | Read whole file for CSS changes |
| `frontend/public/index.html` | ~175 | Small; safe to read whole |
| `backend/app/models.py` | ~80 | Small; safe to read whole |
| `backend/app/schemas.py` | ~60 | Small; safe to read whole |
