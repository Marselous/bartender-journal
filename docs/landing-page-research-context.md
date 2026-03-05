# 🎨 Landing Page Research — Full Context File
> **Purpose:** This file was generated from a live browser research session. Pass it to Claude Code to provide full context about modern, well-designed landing pages, their architectural patterns, and design principles.

---

## 📋 Session Summary

A live browsing session was conducted visiting 7 world-class SaaS/product landing pages. Each was screenshotted and analyzed for design language, hero structure, and architectural patterns. The goal was to identify what makes a fast, modern, and well-organized landing page.

---

## 🌐 Sites Visited & Analyzed

### 1. Linear — https://linear.app
- **Category:** Project management / Dev tooling
- **Design Language:** Dark background (#0A0A0A), large white editorial sans-serif typography, product UI preview embedded below hero
- **Color Palette:** Black, white, subtle purple accents
- **Hero Headline:** *"The product development system for teams and agents"*
- **Subheadline:** *"Purpose-built for planning and building products. Designed for the AI era."*
- **CTA:** Single — "Sign up" (top-right nav) + announcement badge top-right ("New: Linear Diffs (Beta) →")
- **Hero Visual:** Full-width product screenshot (issue tracker UI) starting mid-page
- **Nav Structure:** Logo | Product | Resources | Customers | Pricing | Now | Contact || Log in | Sign up (pill button)
- **Key Design Decisions:**
  - Zero hero image — just text + product
  - Gigantic headline (~80px) signals confidence
  - No gradient, no illustration — pure typographic hierarchy
  - Product shown immediately, no scrolling needed to understand the value

---

### 2. Vercel — https://vercel.com
- **Category:** Cloud deployment / Developer infrastructure
- **Design Language:** Dark grid background, centered layout, dynamic gradient orb below fold, dual CTAs
- **Color Palette:** Near-black, white text, rainbow gradient accent (red/green/blue prism)
- **Hero Headline:** *"Build and deploy on the AI Cloud."*
- **Subheadline:** *"Vercel provides the developer tools and cloud infrastructure to build, scale, and secure a faster, more personalized web."*
- **CTAs:** "▲ Start Deploying" (filled) + "Get a Demo" (outlined)
- **Hero Visual:** Glowing prism/pyramid with colorful spectral light below the text
- **Nav Structure:** Logo | Products ▾ | Resources ▾ | Solutions ▾ | Enterprise | Pricing || Log In | Ask AI | Sign Up
- **Key Design Decisions:**
  - Grid overlay on dark bg creates depth without noise
  - Dual CTA: one for self-serve (Start Deploying), one for enterprise (Get a Demo)
  - "Ask AI" as a nav item signals product identity
  - Spectral gradient visual is brand-memorable and unique

---

### 3. Arc Browser — https://arc.net
- **Category:** Consumer browser / AI product
- **Design Language:** Soft pastel gradients (pink/lavender/cream), playful wavy border between nav and hero, friendly personality
- **Color Palette:** Blue nav bar, warm pastel hero gradient, dark product UI mockup
- **Hero Headline:** *"Meet Dia, the next evolution of Arc"*
- **Subheadline:** *"A familiar design that weaves AI into everyday tasks"*
- **CTA:** Single large pill button — app icon + "Try Dia →" (dark, rounded)
- **Hero Visual:** Large product window mockup showing the Arc browser with Dia AI chat interface
- **Nav Structure:** Logo | Max ✦ | Mobile □ | Developers | Students | Blog
- **Key Design Decisions:**
  - Wavy decorative border between nav and content = strong brand personality
  - Warm pastel palette differentiates in a sea of dark-mode SaaS sites
  - Single, confident CTA — no decision fatigue
  - Product mockup is the content, not decoration

---

### 4. Notion — https://notion.com
- **Category:** Productivity / AI workspace
- **Design Language:** Deep navy (#0D1B3E), illustrated floating characters/emoji, centered layout
- **Color Palette:** Dark navy, white text, blue/indigo accents, colorful illustration characters
- **Hero Headline:** *"Meet the night shift."*
- **Subheadline:** *"Notion agents keep work moving 24/7. They capture knowledge, answer questions, and push projects forward—all while you sleep."*
- **CTAs:** "Get Notion free" (blue filled) + "Request a demo" (blue outlined)
- **Hero Visual:** Product mockup (Notion workspace) with illustrated characters floating around it
- **Announcement Banner:** "New · Introducing Custom Agents: They keep your work moving 24/7. Learn more →"
- **Nav Structure:** Logo | Product ▾ | AI ▾ | Solutions ▾ | Resources ▾ | Enterprise | Pricing | Request a demo || Log in | Get Notion free
- **Key Design Decisions:**
  - Announcement bar at very top for product news
  - Illustrated mascots give warmth/personality to a productivity tool
  - "Night shift" headline uses metaphor — not feature-led, emotion-led
  - Dark navy (not pure black) feels premium and trustworthy

---

### 5. Raycast — https://raycast.com
- **Category:** Developer productivity / macOS launcher
- **Design Language:** Deep black/space background, cinematic product demo AS the hero, minimal text
- **Color Palette:** Near-black, white text, red/orange brand accent, subtle starfield
- **Hero Headline:** *"Magic at your fingertips"*
- **Subheadline:** *"Unlock a new level of productivity. Work smarter..."* (partially hidden by product UI)
- **CTA:** "Download" (top-right, with Apple logo icon)
- **Hero Visual:** Full product window (Raycast launcher with clipboard history + action panel) dominates 70% of viewport
- **Nav Structure:** Logo | Store | Pro | AI | iOS | Windows | Teams | Developers | Blog | Pricing || Log in | ⬛ Download
- **Key Design Decisions:**
  - Product IS the hero — 70% of viewport is the app UI
  - Minimal text because the product explains itself visually
  - Download CTA is persistent in nav — frictionless conversion
  - Dark cinematic feel matches the "power user" audience

---

### 6. Resend — https://resend.com
- **Category:** Email API / Developer tooling
- **Design Language:** Pure black, large editorial serif typography (contrasting with most SaaS sans-serif), moody 3D object photography
- **Color Palette:** Pure black (#000000), white text, no color accents
- **Hero Headline:** *"Email for developers"* (massive serif ~100px)
- **Subheadline:** *"The best way to reach humans instead of spam folders. Deliver transactional and marketing emails at scale."*
- **CTAs:** "Get Started" (white filled, rounded) + "Documentation" (text link)
- **Hero Visual:** A dramatic 3D Rubik's cube rendered in monochromatic metallic texture, right-aligned
- **Nav Structure:** Logo | Features ▾ | Company ▾ | Resources ▾ | Help ▾ | Docs ▾ | AI ▾ | Pricing || Log In | Get Started
- **Key Design Decisions:**
  - Serif headline is bold and unexpected — stands out from all-sans-serif competitors
  - Pure black is more aggressive/confident than dark gray
  - 3D object is artistic and memorable without being decorative fluff
  - "Documentation" as secondary CTA perfectly targets developer audience

---

### 7. Framer — https://framer.com
- **Category:** No-code website builder / Design tool
- **Design Language:** Meta-design — the landing page IS a mosaic of sites built with Framer
- **Color Palette:** Varies — the page is a collage of other sites' colors
- **Hero Structure:** Masonry grid of customer/showcase websites fills the entire viewport
- **CTA:** "Sign up" (top-right nav)
- **Nav Structure:** Logo | Product | Teams | Resources | Community | Support | Enterprise | Pricing || Log in | Sign up
- **Key Design Decisions:**
  - Social proof IS the design — no hero copy needed when the work speaks
  - Masonry layout is dynamic, scrollable, ever-changing
  - Shows diversity of use cases (SaaS, portfolios, agencies, startups) at a glance
  - Confident enough to let customers do the selling

---

## 🏛️ Universal Architectural Pattern

Every single site follows a variation of this structure:

```
┌─────────────────────────────────────────────────────┐
│  STICKY NAV                                         │
│  [Logo]  [Link] [Link] [Link]  [Login] [CTA Button] │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  ANNOUNCEMENT BAR (optional)                        │
│  "New: Feature X → Learn more"                      │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                   HERO SECTION                      │
│                                                     │
│         [Large Bold Headline — 1-2 lines]           │
│         [Subheadline — 1-3 lines]                   │
│                                                     │
│         [Primary CTA]    [Secondary CTA]            │
│                                                     │
│         [Hero Visual: Product / 3D / Illustration]  │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  SOCIAL PROOF                                       │
│  "Trusted by [Company logos in grayscale]"          │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  FEATURE SECTIONS (alternating layout)              │
│  [Visual left + Text right]                         │
│  [Text left + Visual right]                         │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  TESTIMONIALS / CASE STUDIES                        │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  PRICING (optional above fold)                      │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  FINAL CTA SECTION                                  │
│  [Big headline] [Sign up free button]               │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│  FOOTER                                             │
│  [Logo] [Link columns] [Social] [Legal]             │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Design Principles Observed

### Typography
- **Hero headlines:** 64–100px, bold/black weight, 1–2 lines max
- **Subheadlines:** 16–20px, regular weight, 2–4 lines max, ~60% opacity or slightly lighter color
- **Font choices:** Sans-serif dominates (Inter, Geist, custom); Resend uses editorial serif as differentiator
- **Line height:** Tight on headlines (1.0–1.1), comfortable on body (1.5–1.6)

### Color & Backgrounds
| Site | Background | Primary Text | Accent |
|------|-----------|--------------|--------|
| Linear | #0A0A0A (near black) | White | Purple |
| Vercel | #000000 (pure black) | White | Rainbow gradient |
| Arc | Pastel gradient | Dark | Blue |
| Notion | #0D1B3E (navy) | White | Blue |
| Raycast | #000000 (pure black) | White | Red/orange |
| Resend | #000000 (pure black) | White | None |
| Framer | Multi (mosaic) | Multi | Multi |

**Takeaway:** Dark/black backgrounds dominate (5/7 sites). Light or colorful backgrounds are a differentiator.

### CTA Patterns
- **Single CTA:** Arc, Raycast, Resend — high confidence, single focus
- **Dual CTA:** Linear, Vercel, Notion, Framer — primary (free/start) + secondary (demo/docs)
- **CTA Style:** Pill/rounded buttons preferred over sharp corners
- **CTA Copy:** Action-first verbs — "Start Deploying", "Get Started", "Try Dia", "Download"

### Navigation
- All sites: Logo far left, links center, auth/CTA far right
- Max nav links: 6–8 (more use dropdowns ▾ to keep it clean)
- "Log in" is always lower visual weight than "Sign up"
- Sticky positioning on all sites

### Hero Visual Strategies
| Strategy | Sites Using It | Best For |
|----------|---------------|----------|
| Product UI screenshot/mockup | Linear, Arc, Notion, Raycast | Apps with visual UI |
| Abstract 3D object | Resend, Vercel | Dev tools, APIs |
| Customer showcase mosaic | Framer | Platforms/builders |
| Pure typography | (rare) | Bold/confident brands |

### Spacing & Layout
- **Max content width:** ~1200–1400px, centered
- **Hero padding top:** 80–120px below nav
- **Section spacing:** 80–160px between sections
- **White space is generous** — crowding is the anti-pattern

---

## 💡 Key Takeaways for Building Landing Pages

1. **Restraint is the strategy.** Every great page removes more than it adds.
2. **The headline is everything.** 80% of visitors read only the headline. Make it count.
3. **Show the product fast.** Don't make users scroll to see what they're signing up for.
4. **Dark mode is default for dev/tech.** Light mode works for consumer/creative tools.
5. **One primary CTA per fold.** Decision fatigue kills conversion.
6. **Social proof near the top.** Company logos or user counts reduce anxiety.
7. **Navigation should disappear visually.** Functional, not decorative.
8. **Mobile-first sizing.** All sites use fluid typography and responsive grids.
9. **Performance matters.** These pages load in <2s. No heavy frameworks above fold.
10. **Personality through detail.** Wavy borders (Arc), serif type (Resend), starfield (Raycast) — one unexpected element makes a page memorable.

---

## 🗂️ File Structure Recommendation for Implementation

If building a landing page based on these patterns:

```
/
├── index.html (or page.tsx)
├── components/
│   ├── Nav.tsx
│   ├── AnnouncementBar.tsx
│   ├── Hero.tsx
│   ├── LogoCloud.tsx
│   ├── FeatureSection.tsx
│   ├── Testimonials.tsx
│   ├── Pricing.tsx
│   ├── FinalCTA.tsx
│   └── Footer.tsx
├── styles/
│   └── globals.css (tokens: colors, spacing, typography)
└── assets/
    ├── product-screenshots/
    └── icons/
```

---

## 📸 Screenshots Captured During Session

The following pages were live-screenshotted during the session:

| # | Site | URL | Screenshot Description |
|---|------|-----|----------------------|
| 1 | Linear | https://linear.app | Dark hero, massive white headline, product UI preview |
| 2 | Vercel | https://vercel.com | Dark grid bg, centered headline, spectral prism gradient |
| 3 | Arc | https://arc.net | Pastel gradient, wavy nav border, "Try Dia" CTA |
| 4 | Notion | https://notion.com | Navy bg, illustrated characters, dual blue CTAs |
| 5 | Raycast | https://raycast.com | Black bg, product window dominates 70% of viewport |
| 6 | Resend | https://resend.com | Pure black, giant serif headline, metallic Rubik's cube |
| 7 | Framer | https://framer.com | Masonry mosaic grid of customer websites |

---

## 🤖 Instructions for Claude Code

When receiving this file, Claude Code should understand:

1. **Research was done live** — these are current (March 2026) production landing pages
2. **This is reference material** for building a modern landing page
3. **The architectural pattern in this file** is the agreed-upon structure to follow
4. **Design decisions** documented above represent the industry consensus for SaaS/dev-tool landing pages
5. **The user's goal** is to build something "very simple but very well organised in its architecture"

### Suggested first prompt to Claude Code after providing this file:
> "Based on the landing page research in this context file, build me a [your product type] landing page following the universal architectural pattern. Use the design principles documented — dark background, large hero headline, single CTA, product visual below fold."

---

*Generated: March 2026 | Session: Live browser research via Claude in Chrome*
