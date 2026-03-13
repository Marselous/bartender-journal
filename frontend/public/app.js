"use strict";

/* ── State ─────────────────────────────────────────────────────────────── */
const state = {
  apiBase:         localStorage.getItem("apiBase") || "",
  token:           localStorage.getItem("token") || "",
  currentUsername: localStorage.getItem("username") || "",
  nextCursor:      null,
  loading:         false,
};

/* ── Helpers ───────────────────────────────────────────────────────────── */
const el = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/"/g, "&quot;"); }

function api(url) {
  const base = state.apiBase.replace(/\/$/, "");
  return base ? `${base}${url}` : url;
}

async function fetchJson(url, opts = {}) {
  const headers = { "content-type": "application/json", ...(opts.headers || {}) };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(url, { ...opts, headers });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${t}`);
  }
  return res.json();
}

async function checkApiReachable() {
  const url = api("/healthz");
  if (!url.startsWith("http")) return { ok: false, error: "Enter a valid API base URL (e.g. http://HOST:30001)" };
  const res = await fetch(url, { method: "GET" }).catch(() => null);
  if (!res) return { ok: false, error: "Cannot connect — check URL and network" };
  if (!res.ok) return { ok: false, error: `API returned ${res.status}` };
  const data = await res.json().catch(() => ({}));
  return data.ok ? { ok: true } : { ok: false, error: "Invalid health response" };
}

/* ── Toast ─────────────────────────────────────────────────────────────── */
const toastEl = el("toast");
let toastTimer;
function toast(msg, danger = false) {
  clearTimeout(toastTimer);
  toastEl.textContent = msg;
  toastEl.classList.toggle("danger", danger);
  toastEl.style.display = "block";
  toastTimer = setTimeout(() => (toastEl.style.display = "none"), 2800);
}

/* ── Live dot ───────────────────────────────────────────────────────────── */
async function updateLiveDot() {
  const dot = document.querySelector(".live-dot");
  if (!dot) return;
  if (!state.apiBase.startsWith("http")) { dot.style.background = "var(--muted)"; dot.style.boxShadow = "none"; return; }
  const result = await checkApiReachable().catch(() => ({ ok: false }));
  if (result.ok) {
    dot.style.background = "var(--success)";
    dot.style.boxShadow = "0 0 6px var(--success)";
  } else {
    dot.style.background = "var(--danger)";
    dot.style.boxShadow = "0 0 6px var(--danger)";
  }
}

/* ── Auth / user badge ──────────────────────────────────────────────────── */
function updateUserBadge() {
  const badge = el("userBadge");
  if (!badge) return;
  if (state.token && state.currentUsername) {
    badge.textContent = `Signed in as ${state.currentUsername}`;
  } else if (state.token) {
    badge.textContent = "Signed in";
  } else {
    badge.textContent = "Guest";
  }
}

/* ── Modal ──────────────────────────────────────────────────────────────── */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add("active");
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove("active");
}

/* ── Relative time ──────────────────────────────────────────────────────── */
function relativeTime(iso) {
  try {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60)  return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 86400 * 2) return "Yesterday";
    return new Date(iso).toLocaleDateString();
  } catch { return iso; }
}

/* ── Avatar color from name hash ────────────────────────────────────────── */
const AVATAR_COLORS = ["#ffcc66","#6aaeff","#c084fc","#4ade80","#fb923c","#f472b6","#34d399","#60a5fa"];
function avatarColor(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

/* ── Post type field switching ───────────────────────────────────────────── */
function setPostType(type) {
  el("postBodyWrap").style.display  = type === "text"  ? "block" : "none";
  el("postLinkWrap").style.display  = type === "link"  ? "block" : "none";
  el("postPhotoWrap").style.display = type === "photo" ? "block" : "none";

  document.querySelectorAll(".type-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.type === type);
  });
}

/* ── Library rendering ───────────────────────────────────────────────────── */
function renderLibraryItems(items) {
  if (!items || !items.length) return `<div style="color:var(--muted);font-size:13px;">No items found.</div>`;
  return `<ul class="library-list" style="list-style:none;margin:0;padding:0;">${items.map((item) => {
    const title = escapeHtml(item.name || item.title || item.entry || "");
    const rawTags = item.tags || item.category ? [item.category, ...(item.tags || [])].filter(Boolean) : [];
    const tags = rawTags.map((t) => `<span class="tag-chip">${escapeHtml(t)}</span>`).join("");
    return `<li class="library-item">
      <div class="library-item-title">${title}</div>
      ${tags ? `<div class="library-item-tags">${tags}</div>` : ""}
    </li>`;
  }).join("")}</ul>`;
}

async function loadLibrary(which) {
  el("libraryOut").innerHTML = `<div style="color:var(--muted);font-size:13px;">Loading…</div>`;
  document.querySelectorAll(".lib-tab").forEach((b) => b.classList.toggle("active", b.dataset.library === which));
  try {
    const data = await fetchJson(api(`/library/${which}`));
    // data may be array or object with items array
    const items = Array.isArray(data) ? data : (data.items || data[which] || []);
    el("libraryOut").innerHTML = renderLibraryItems(items);
  } catch (e) {
    el("libraryOut").innerHTML = `<div style="color:var(--danger);font-size:13px;">Error: ${escapeHtml(e.message)}</div>`;
  }
}

/* ── Post card ───────────────────────────────────────────────────────────── */
function postCard(p) {
  const article = document.createElement("article");
  article.className = "post-card";
  article.dataset.postId = p.id;

  const author = p.author_name || "Guest";
  const initial = author[0].toUpperCase();
  const color = avatarColor(author);
  const title = p.title ? escapeHtml(p.title) : escapeHtml(p.type);
  const body = p.body ? `<p class="post-body">${escapeHtml(p.body)}</p>` : "";
  const link = p.link_url ? `<div class="post-link"><a href="${escapeAttr(p.link_url)}" target="_blank" rel="noreferrer noopener">${escapeHtml(p.link_url)}</a></div>` : "";
  const img  = p.image_url ? `<img class="post-image" src="${escapeAttr(p.image_url)}" alt="post image" loading="lazy" />` : "";
  const commentCount = p.comment_count ?? 0;
  const type = p.type || "text";

  article.innerHTML = `
    <header class="post-header">
      <div class="post-author">
        <div class="avatar" style="background:${color};">${escapeHtml(initial)}</div>
        <div>
          <div class="author-name">${escapeHtml(author)}</div>
          <time class="post-time">${relativeTime(p.created_at)}</time>
        </div>
      </div>
      <span class="type-badge type-${escapeAttr(type)}">${escapeHtml(type)}</span>
    </header>
    <h3 class="post-title">${title}</h3>
    ${body}${link}${img}
    <footer class="post-footer">
      <button class="btn-ghost btn-sm toggleComments">&#x1F4AC; ${commentCount} comment${commentCount === 1 ? "" : "s"}</button>
    </footer>
    <div class="comments-panel">
      <div class="comment-form">
        <div>
          <label>Your name (optional)</label>
          <input class="input commentAuthor" placeholder="Guest" maxlength="80" />
        </div>
        <div>
          <label>Comment</label>
          <input class="input commentBody" placeholder="Write a comment…" maxlength="5000" />
        </div>
      </div>
      <div class="comment-actions">
        <button class="btn-primary btn-sm submitComment">Post comment</button>
        <button class="btn-ghost btn-sm refreshComments">Refresh</button>
      </div>
      <div class="comment-list"></div>
    </div>
  `;
  return article;
}

/* ── Skeleton card ───────────────────────────────────────────────────────── */
function skeletonCard() {
  const div = document.createElement("div");
  div.className = "skeleton-card";
  div.innerHTML = `
    <div class="skel-line h16"></div>
    <div class="skel-line h12"></div>
    <div class="skel-line h8"></div>
  `;
  return div;
}

/* ── Comments ────────────────────────────────────────────────────────────── */
async function renderComments(postEl) {
  const postId = postEl.dataset.postId;
  const list = postEl.querySelector(".comment-list");
  list.innerHTML = `<div style="color:var(--muted);font-size:13px;">Loading…</div>`;
  try {
    const comments = await fetchJson(api(`/posts/${postId}/comments`));
    if (!comments.length) { list.innerHTML = `<div style="color:var(--muted);font-size:13px;">No comments yet.</div>`; return; }
    list.innerHTML = "";
    comments.forEach((c) => {
      const item = document.createElement("div");
      item.className = "comment-item";
      item.innerHTML = `
        <div class="comment-meta">
          <span>${escapeHtml(c.author_name || "Guest")}</span>
          <span>${relativeTime(c.created_at)}</span>
        </div>
        <div class="comment-body">${escapeHtml(c.body)}</div>
      `;
      list.appendChild(item);
    });
  } catch (e) {
    list.innerHTML = `<div style="color:var(--danger);font-size:13px;">Error: ${escapeHtml(e.message)}</div>`;
  }
}

async function submitComment(postEl) {
  const postId = postEl.dataset.postId;
  const author = postEl.querySelector(".commentAuthor").value.trim() || null;
  const body   = postEl.querySelector(".commentBody").value.trim();
  if (!body) return toast("Comment body required.", true);

  const btn = postEl.querySelector(".submitComment");
  btn.disabled = true;
  try {
    await fetchJson(api(`/posts/${postId}/comments`), {
      method: "POST",
      body: JSON.stringify({ author_name: author, body }),
    });
    postEl.querySelector(".commentBody").value = "";
    toast("Comment posted.");
    await renderComments(postEl);
    await loadFeed(true);
  } catch (e) {
    toast(`Comment error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

/* ── Feed ────────────────────────────────────────────────────────────────── */
async function loadFeed(reset = false) {
  if (state.loading) return;
  state.loading = true;
  const loadMoreBtn = el("loadMore");
  if (loadMoreBtn) loadMoreBtn.disabled = true;

  const feedEl = el("feed");
  if (reset) {
    feedEl.innerHTML = "";
    // show skeletons
    for (let i = 0; i < 3; i++) feedEl.appendChild(skeletonCard());
  }

  try {
    const qs = new URLSearchParams({ limit: "10" });
    if (!reset && state.nextCursor) qs.set("cursor", state.nextCursor);
    const data = await fetchJson(api(`/posts?${qs.toString()}`));

    if (reset) feedEl.innerHTML = "";
    data.items.forEach((p) => feedEl.appendChild(postCard(p)));
    state.nextCursor = data.next_cursor || null;
    if (loadMoreBtn) {
      loadMoreBtn.style.display = state.nextCursor ? "inline-block" : "none";
    }
  } catch (e) {
    if (reset) feedEl.innerHTML = "";
    toast(`Feed error: ${e.message}. Set API base URL first.`, true);
  } finally {
    state.loading = false;
    if (loadMoreBtn) loadMoreBtn.disabled = false;
  }
}

/* ── Post submit ─────────────────────────────────────────────────────────── */
async function submitPost() {
  const type       = el("postType").value;
  const author_name = el("postAuthor").value.trim() || null;
  const title      = el("postTitle").value.trim() || null;
  const body       = el("postBody").value.trim() || null;
  const link_url   = el("postLink").value.trim() || null;
  const image_url  = el("postImage").value.trim() || null;

  const btn = el("submitPost");
  btn.disabled = true;
  try {
    await fetchJson(api("/posts"), {
      method: "POST",
      body: JSON.stringify({ type, title, body, link_url, image_url, author_name }),
    });
    el("postBody").value = "";
    el("postLink").value = "";
    el("postImage").value = "";
    toast("Posted.");
    await loadFeed(true);
  } catch (e) {
    toast(`Post error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

/* ── Auth ────────────────────────────────────────────────────────────────── */
async function submitRegister() {
  const email    = el("regEmail").value.trim();
  const username = el("regUsername").value.trim();
  const password = el("regPassword").value;
  if (!email || !username || !password) return toast("Email, username and password are required.", true);

  const btn = el("submitRegister");
  btn.disabled = true;
  try {
    await fetchJson(api("/auth/register"), {
      method: "POST",
      body: JSON.stringify({ email, username, password }),
    });
    toast("Registered. Now sign in.");
    closeModal("registerModal");
  } catch (e) {
    toast(`Register error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

async function submitLogin() {
  const username = el("loginUsername").value.trim();
  const password = el("loginPassword").value;
  if (!username || !password) return toast("Username and password required.", true);

  const btn = el("submitLogin");
  btn.disabled = true;
  try {
    const data = await fetchJson(api("/auth/login"), {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    state.token = data.access_token;
    state.currentUsername = username;
    localStorage.setItem("token", state.token);
    localStorage.setItem("username", state.currentUsername);
    updateUserBadge();
    toast("Signed in.");
    closeModal("loginModal");
  } catch (e) {
    toast(`Login error: ${e.message}`, true);
  } finally {
    btn.disabled = false;
  }
}

/* ── Settings / API base URL ─────────────────────────────────────────────── */
async function saveApiBase() {
  const url = el("apiBase").value.trim();
  state.apiBase = url;
  localStorage.setItem("apiBase", url);

  if (!url) { toast("Enter an API URL (e.g. http://minikube-ip:30001) and click Save."); return; }

  const btn = el("saveApiBase");
  btn.disabled = true;
  try {
    const result = await checkApiReachable();
    if (result.ok) {
      toast("API connected. Loading feed…");
      await updateLiveDot();
      await loadFeed(true);
    } else {
      toast(`Cannot reach API: ${result.error || "No route to host"}`, true);
      await updateLiveDot();
    }
  } catch (e) {
    const msg = e.message || String(e);
    const hint = /Failed to fetch|Load failed|NetworkError/.test(msg)
      ? " Backend unreachable — check URL and that the server is running." : "";
    toast(`Cannot reach API.${hint} (${msg})`, true);
  } finally {
    btn.disabled = false;
  }
}

/* ── Wire-up ──────────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  // Settings drawer
  el("apiBase").value = state.apiBase;
  el("saveApiBase").addEventListener("click", saveApiBase);
  el("settingsToggle").addEventListener("click", () => {
    const d = el("settingsDrawer");
    d.classList.toggle("open");
  });

  // Type tabs
  document.querySelectorAll(".type-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      el("postType").value = tab.dataset.type;
      setPostType(tab.dataset.type);
    });
  });

  // Post submit
  el("submitPost").addEventListener("click", submitPost);

  // Load more
  el("loadMore").addEventListener("click", () => loadFeed(false));

  // Scroll-to wall CTA
  const ctaWall = el("ctaWall");
  if (ctaWall) {
    ctaWall.addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("wall").scrollIntoView({ behavior: "smooth" });
    });
  }

  // Auth modals
  el("openRegister").addEventListener("click", () => openModal("registerModal"));
  el("openLogin").addEventListener("click", () => openModal("loginModal"));
  el("submitRegister").addEventListener("click", submitRegister);
  el("submitLogin").addEventListener("click", submitLogin);

  // Close modals
  document.querySelectorAll(".modal-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-close-modal");
      if (id) closeModal(id);
    });
  });
  document.querySelectorAll(".modal").forEach((m) => {
    m.addEventListener("click", (e) => { if (e.target === m) m.classList.remove("active"); });
  });

  // Hero CTA sign up
  const heroSignup = el("heroSignup");
  if (heroSignup) heroSignup.addEventListener("click", () => openModal("registerModal"));

  // Library tabs
  document.querySelectorAll(".lib-tab").forEach((b) => {
    b.addEventListener("click", () => loadLibrary(b.dataset.library));
  });

  // Feed click delegation (comments, submit)
  el("feed").addEventListener("click", async (e) => {
    const postEl = e.target.closest(".post-card");
    if (!postEl) return;
    if (e.target.classList.contains("toggleComments")) {
      const panel = postEl.querySelector(".comments-panel");
      const open = panel.style.display === "block";
      panel.style.display = open ? "none" : "block";
      if (!open) await renderComments(postEl);
    }
    if (e.target.classList.contains("refreshComments")) await renderComments(postEl);
    if (e.target.classList.contains("submitComment")) await submitComment(postEl);
  });

  // Initial state
  setPostType("text");
  updateUserBadge();
  updateLiveDot();
  if (state.apiBase && state.apiBase.startsWith("http")) loadFeed(true);

  // Flickering grid hero background
  initFlickeringGrid("heroGrid", {
    squareSize:    4,
    gridGap:       6,
    color:         "#0D1526",
    maxOpacity:    0.5,
    flickerChance: 0.3,
  });
});

/* ── Flickering grid (canvas) ─────────────────────────────────────────────
 * Ported from FlickeringGrid React component (kokonut UI).
 * Draws a grid of small squares that randomly flicker their opacity.
 * Pauses automatically when off-screen (IntersectionObserver).
 * Resizes to container via ResizeObserver.
 * ───────────────────────────────────────────────────────────────────────── */
function initFlickeringGrid(containerId, opts = {}) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const {
    squareSize    = 4,
    gridGap       = 6,
    color         = "rgb(0,0,0)",
    maxOpacity    = 0.3,
    flickerChance = 0.3,
  } = opts;

  // Resolve color once into an "rgba(r,g,b," prefix
  function toRGBAPrefix(cssColor) {
    const tmp = document.createElement("canvas");
    tmp.width = tmp.height = 1;
    const ctx = tmp.getContext("2d");
    ctx.fillStyle = cssColor;
    ctx.fillRect(0, 0, 1, 1);
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    return `rgba(${r},${g},${b},`;
  }
  const rgbaPrefix = toRGBAPrefix(color);

  const canvas = document.createElement("canvas");
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  let cols, rows, squares, dpr;
  let rafId = null;
  let isInView = true;   // assume in-view on init; IntersectionObserver overrides
  let lastTime = 0;

  function setup(w, h) {
    dpr    = window.devicePixelRatio || 1;
    canvas.width        = w * dpr;
    canvas.height       = h * dpr;
    canvas.style.width  = w + "px";
    canvas.style.height = h + "px";
    cols = Math.floor(w / (squareSize + gridGap));
    rows = Math.floor(h / (squareSize + gridGap));
    squares = new Float32Array(cols * rows);
    for (let i = 0; i < squares.length; i++) {
      squares[i] = Math.random() * maxOpacity;
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const cell = (squareSize + gridGap) * dpr;
    const sq   = squareSize * dpr;
    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        ctx.fillStyle = rgbaPrefix + squares[i * rows + j] + ")";
        ctx.fillRect(i * cell, j * cell, sq, sq);
      }
    }
  }

  function animate(time) {
    if (!isInView) return;
    const delta = lastTime ? (time - lastTime) / 1000 : 0;
    lastTime = time;
    for (let i = 0; i < squares.length; i++) {
      if (Math.random() < flickerChance * delta) {
        squares[i] = Math.random() * maxOpacity;
      }
    }
    draw();
    rafId = requestAnimationFrame(animate);
  }

  function startLoop() {
    if (rafId) return;
    lastTime = 0;
    rafId = requestAnimationFrame(animate);
  }

  function stopLoop() {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
  }

  // Size tracking
  const resizeObs = new ResizeObserver(() => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w && h) { setup(w, h); draw(); }
  });
  resizeObs.observe(container);

  // Pause when off-screen
  const intersectObs = new IntersectionObserver(([entry]) => {
    isInView = entry.isIntersecting;
    if (isInView) startLoop(); else stopLoop();
  }, { threshold: 0 });
  intersectObs.observe(canvas);

  // Defer initial setup to next frame so the hero has computed its dimensions
  requestAnimationFrame(() => {
    const w0 = container.clientWidth  || container.offsetWidth;
    const h0 = container.clientHeight || container.offsetHeight;
    if (w0 && h0) {
      setup(w0, h0);
      draw();
      if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        startLoop();
      }
    }
  });
}
