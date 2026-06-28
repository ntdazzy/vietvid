---
name: Vyra
description: Premium dark-cinematic design system for Vyra — an AI Vietnamese-voice marketing-video SaaS. Violet→indigo→blue brand on a near-black base, glass surfaces, one accent per screen, honest (no fabricated stats).
version: 1.0.0
locale: vi-VN
mode: dark
colors:
  # Base / surfaces (near-black, slightly blue-tinted)
  background: "#06070D"
  surface: "#0B0D16"
  surface-2: "#12141F"
  surface-elevated: "#1A1C2A"
  border: "rgba(255,255,255,0.08)"
  # Brand (violet → indigo → blue)
  primary: "#7C4DFF"        # violet-500 — the brand anchor (CTA, selection, value)
  secondary: "#6366F1"      # indigo-500 — gradient midpoint
  accent: "#3B82F6"         # brand blue-500 — gradient end
  primary-gradient: "linear-gradient(135deg,#7C4DFF 0%,#6366F1 50%,#3B82F6 100%)"
  # Text (ink) levels
  text: "#F4F5FA"           # ink-high
  text-muted: "#B4B7C7"     # ink-medium
  text-subtle: "#7E8298"    # ink-low
  text-disabled: "#4B4E61"  # ink-disabled
  # Semantic
  success: "#34D399"
  warning: "#FBBF24"        # also "hold" (credit reserved)
  error: "#F87171"          # also "danger"
  info: "#60A5FA"
  refund: "#22D3EE"         # cyan — credit returned
  # Per-screen accent hues (one accent per screen; same brand family)
  accent-violet: "#7C4DFF"
  accent-emerald: "#10B981"
  accent-amber: "#F59E0B"
  accent-sky: "#0EA5E9"
  accent-rose: "#F43F5E"
  accent-cyan: "#06B6D4"
  accent-slate: "#94A3B8"
typography:
  display: "Be Vietnam Pro"     # headings — ONLY diacritic-safe heading font
  body: "Inter"                 # paragraphs, UI
  numeric: "Space Grotesk"      # NUMBERS ONLY (credits, stats), tabular-nums
  mono: "Geist Mono"
  display-weights: [600, 700, 800]
  body-weights: [400, 500, 600]
  numeric-weights: [500, 600, 700]
  heading-tracking: "-0.02em"
  body-leading: "1.65"
radius:
  sm: "8px"
  md: "12px"     # lg token in code — inputs, chips, small cards
  lg: "16px"     # xl token — buttons, cards
  xl: "20px"     # 2xl — large cards, hero, big buttons
  2xl: "28px"    # 3xl — feature panels
  full: "9999px" # badges, avatars, pills
spacing:
  unit: "4px"
  section-y: "96px"      # py-24 — marketing section rhythm
  card-pad: "20px"       # p-5
  container-max: "1152px" # max-w-6xl (marketing); app uses max-w-7xl 1280px
shadows:
  glow-sm: "0 0 16px rgba(124,77,255,.35)"
  glow-md: "0 0 32px rgba(124,77,255,.45)"
  glow-lg: "0 0 64px rgba(124,77,255,.40)"
  glow-blue: "0 0 40px rgba(59,130,246,.40)"
  glow-success: "0 0 28px rgba(52,211,153,.40)"
  inset-highlight: "inset 0 1px 0 rgba(255,255,255,.06)"
  cta: "0 0 0 1px rgba(124,77,255,.5), 0 8px 40px -8px rgba(99,102,241,.55)"
---

# Vyra — Design System

Vyra turns one product photo into a 60-second Vietnamese-voice marketing video. The interface has to feel **premium and cinematic, never "AI-generic"**: near-black canvas, a single violet→blue brand gradient used with intent, glass surfaces with thin light borders, and a per-screen accent so each area reads as its own place. Honesty is part of the brand — we never show fabricated metrics.

> Render target: **dark mode only**, Vietnamese-first copy (`lang="vi"`).

## 1. Color

**Base is near-black, not pure black.** `#06070D` canvas with three darker-to-lighter glass surfaces (`#0B0D16`, `#12141F`, `#1A1C2A`). Borders are white at 6–8% opacity, never solid grey lines.

**Brand = one gradient, used sparingly.** `linear-gradient(135deg,#7C4DFF,#6366F1,#3B82F6)` (violet→indigo→blue). It belongs on the primary CTA, headline highlights (`.text-gradient`), and selection states — **not** spread across backgrounds. The full violet scale (50 `#F2EEFF` → 900 `#2E1772`, anchor 500 `#7C4DFF`) is available for tints.

**Text uses 4 ink levels:** high `#F4F5FA` (titles), medium `#B4B7C7` (body), low `#7E8298` (hints/labels), disabled `#4B4E61`.

**Semantic colors map to the credit-wallet domain:** success `#34D399`, hold/warning `#FBBF24` (credit reserved), refund `#22D3EE` (credit returned), danger `#F87171`, info `#60A5FA`. Use the hold/refund colors literally for wallet states.

**Per-screen accent system (signature).** Each screen/feature picks ONE accent from a fixed palette so the app is scannable while staying on-brand. Each accent ships a coordinated set: tile gradient, icon tint, glow rgba, focus ring, divider line, chip, text, gradient, and bar.

| Accent | Hue pair | Typical screen |
|---|---|---|
| violet `#7C4DFF` | violet→indigo | create / default / templates |
| emerald `#10B981` | emerald→teal | reports / analytics |
| amber `#F59E0B` | amber→orange | affiliate / earnings |
| sky `#0EA5E9` | sky→blue | team |
| rose `#F43F5E` | rose→pink | brand-kits / KOL lookbook |
| cyan `#06B6D4` | cyan→teal | API / compose |
| slate `#94A3B8` | slate | settings |

Rule: **one accent per screen.** Never mix two accent families on the same view; the brand violet is the only cross-screen constant (CTAs, selection).

## 2. Typography

Three roles, three fonts — do not substitute:

- **Display — Be Vietnam Pro** (600/700/800). The ONLY heading font, because it is the only one with safe Vietnamese diacritics. Applied to `h1–h4`, headline tracking `-0.02em`.
- **Body — Inter** (400/500/600). Paragraphs, labels, UI text. Latin + Vietnamese subsets.
- **Numeric — Space Grotesk** (500/600/700), `tabular-nums`. **NUMBERS ONLY** — credits, stats, prices, counts. **Never wrap Vietnamese words in this font** (it has no diacritics — they vanish). This is a hard rule.
- **Mono — Geist Mono.** Code, tokens, IDs.

**Type scale (px / line-height / weight):**

| Role | Size | LH | Weight | Notes |
|---|---|---|---|---|
| Display / hero | 48–60 | 1.05 | 800 | marketing headlines, `.text-gradient` highlight word |
| H1 (screen title) | 30 | 1.1 | 700 | ScreenHero |
| H2 | 24 | 1.15 | 700 | section heads |
| H3 | 20 | 1.2 | 600 | card titles |
| Body | 14–16 | 1.65 | 400 | paragraphs, max ~65ch |
| Label | 14 | 1.4 | 500 | form labels (ink-medium) |
| Small | 13 | 1.4 | 400 | hints |
| Caption | 11–12 | 1.3 | 500 | chips, badges, tracking-wide |
| Stat value | 24 | 1.1 | 700 | Space Grotesk, tabular |

Emphasis inside a headline = italic/bold of the **same** font, never a second font.

## 3. Spacing

4px base unit. Marketing sections breathe at `py-24` (96px) / `lg:py-28`. Cards pad at 20–24px. Containers cap at `max-w-6xl` (1152px) for marketing and `max-w-7xl` (1280px) for the app shell; never edge-to-edge on wide screens. Gaps: 10–20px between cards (`gap-2.5`…`gap-5`). Bottom padding slightly larger than top, optically.

## 4. Layout

- **Dark canvas + a single soft violet halo at the top** (`--mesh-bg`: one radial `rgba(124,77,255,.10)` at 50% -6% over `#06070D`). Explicitly **not** a violet-cyan-pink mesh — that rainbow mesh is the #1 AI tell and is banned.
- **CSS Grid over flex-percentage math.** `grid grid-cols-1 md:grid-cols-3`, not `w-[calc(33%-1rem)]`.
- **Hero uses `min-h-[100dvh]`**, never `h-screen` (iOS Safari jump).
- **Asymmetry over centered symmetry** for heroes (split / left-content + right-asset).
- **Per-screen ScreenHero** at the top of every app screen: a glass-bordered panel with an accent icon-tile, title, subtitle, optional action, and a stat row.
- **Full-bleed film grain** overlay (`.grain`, opacity .045, `mix-blend-overlay`, `z-60`, pointer-events-none) sits above everything to kill digital flatness.
- Reveal-on-scroll for marketing sections (content animates in once on enter).

## 5. Components

**Buttons** (`rounded-xl`, `transition-all 200ms`, focus ring `violet-500/60` + 2px offset on `bg-base`, disabled `opacity-50` + `text-disabled`, tactile `active:scale-[.98]`):
- `primary` — `bg-grad-brand` text-white, CTA shadow `0 0 0 1px rgba(124,77,255,.5), 0 8px 40px -8px rgba(99,102,241,.55)`, hover → `glow-md` + brightness-110.
- `glass` — `.glass` surface, hover lightens to white/8.
- `ghost` — text-only, hover white/5 wash.
- `outline` — 1px white/12 border, hover violet border + `glow-sm`.
- Sizes: `sm` h-9 / `md` h-11 / `lg` h-[3.25rem] `rounded-2xl`.

**Surfaces / cards:**
- `.glass` — `border-white/8 bg-white/4 backdrop-blur-xl` + inset top highlight.
- `.glass-bordered` — gradient-masked 1px border (violet→blue→white fade) on `bg-white/3 backdrop-blur-xl`, `rounded-xl`. Use for hero panels and primary cards.
- Use a card ONLY when elevation communicates hierarchy; otherwise group with dividers / negative space.

**Badges / chips** (`rounded-full px-2.5 py-1 text-[11px] tracking-wide`): tones neutral, brand (violet), hold (amber), success, refund (cyan), danger — each `bg/12 + text + border/30`.

**Inputs** (`rounded-lg border-white/10 bg-white/3 px-3 py-2.5`): focus → `border-violet-500/50 + ring-violet-500/25`. Selectable chip-group: selected = `border-violet-500/60 bg-violet-500/15 + glow-sm`.

**ScreenHero / StatTile** — the per-screen identity block. StatTile renders its value in `font-numeric tabular`.

**HoverVideo** — a poster image that lazy-loads (`preload=none`) and cross-fades to a short looping clip on hover; used on KOL faces so a portrait "comes alive." Should also scale up slightly on hover.

**MiniReel** — Ken-Burns image + typed-caption overlay; the "video preview" motif.

**Icons** — Lucide, single stroke weight, tinted with the screen's accent.

## 6. Motion

Signature easing `cubic-bezier(.22,1,.36,1)`, durations 200–600ms.
- `fade-up` (.6s) and reveal-on-scroll (whileInView, once, y-offset ~14px, staggered children).
- Ambient loops (subtle): `glow-pulse` 2.4s, `float` 6s, `aurora` 16s, `shimmer` 1.8s (skeletons), `marquee` 42s linear (output gallery), Ken-Burns scale 1→1.07, `caret-blink` for the script typewriter.
- Brand intro: logo stroke draw-on + node pop.
- Tactile press `scale-[.98]` on all interactive elements.
- **`prefers-reduced-motion: reduce` kills every animation/transition** (global override). Honor it.

## 7. Voice

Vietnamese-first, premium, direct. Lead with what the user can DO. Specific over hype. Transparent about money ("hiện ~X credit trước khi tạo", "hoàn 100% nếu lỗi hệ thống"). No exclamation-mark success messages, no "Oops!", no AI clichés (elevate/seamless/unleash). Tagline: **"Tạo video bán hàng, giọng Việt thật."** Positioned to beat autovis.ai on real Vietnamese voice + price transparency.

## 8. Brand

Vyra = AI Vietnamese marketing-video studio. Logo is a violet orbit-and-node mark on the brand gradient. Theme color `#06070D`. The feeling: a high-end film/creator tool, not a generic SaaS dashboard. Confident, cinematic, trustworthy with money.

## 9. Anti-patterns (do NOT do)

- ❌ Violet-cyan-pink **rainbow mesh** backgrounds. One soft violet halo only.
- ❌ Brand violet sprayed everywhere. Violet = intent (CTA / selection / value), not decoration.
- ❌ A row of **4 identical cards** as a decorative feature strip. Vary size/layout (zig-zag, bento, asymmetric).
- ❌ More than **one glow per screen**; glass on literally everything.
- ❌ **Fabricated stats** ("5,000+ creators", "1M views"). Vyra is new — state real capability only.
- ❌ **Vietnamese words in the numeric font** (Space Grotesk) — diacritics disappear. Numbers only.
- ❌ `h-screen` heroes (use `min-h-[100dvh]`); flex `%` math (use Grid).
- ❌ Pure-black `#000` backgrounds or solid-grey borders.
- ❌ Untasteful / revealing AI human imagery. People are fully clothed, business-appropriate, natural (not glossy "AI model").
- ❌ Centered-symmetric hero by default when variance is wanted.
