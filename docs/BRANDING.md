# BuildTrack Branding Guide

**Version:** 1.0 — UI/UX Agent (Agent 4/5)
**Company:** BuildTrack — Residential & Commercial Building Startup

## 1. Brand Positioning

- **Tagline:** "Build with Confidence. Track Every Step."
- **Promise:** Transparent pricing, on-time delivery, daily progress tracking.
- **Tone:** Professional, direct, trustworthy. No jargon. Short sentences. Numbers over adjectives.
- **Voice examples:**
  - Hero: "Your Dream Build, Delivered On Time and On Budget."
  - Sub: "Licensed builders, upfront fixed quotes, and live photo updates from foundation to handover."
  - CTA: "Get Free Quote" / "View Our Work" / "Talk to a Builder"

## 2. Colors

Primary palette — construction orange + dark slate. High contrast, works on site photos.

| Token | Hex | Usage |
|---|---|---|
| `--bt-orange` | `#F26A1B` | Primary CTA, links, active states, logo mark |
| `--bt-orange-dark` | `#C94F0A` | CTA hover, gradients |
| `--bt-orange-light` | `#FFF0E3` | Tint backgrounds, badges |
| `--bt-slate-900` | `#1A2430` | Header/footer bg, headings |
| `--bt-slate-700` | `#344054` | Body text |
| `--bt-slate-500` | `#667085` | Muted text |
| `--bt-slate-100` | `#F2F4F7` | Section alt bg |
| `--bt-white` | `#FFFFFF` | Cards, base |
| `--bt-success` | `#12805C` | Trust badges, "Licensed & Insured" |
| `--bt-warning` | `#B54708` | Alerts only |

Accessibility: white on `#F26A1B` = ~3.1:1 — use only for large/bold text. Body CTAs use white on `#1A2430` with orange accent, or `#1A2430` text on orange button for AA. Primary button defined in `theme.css` uses slate text on orange for contrast.

## 3. Typography

- **Headings:** `Archivo`, `Inter` fallback — 700/800, tight letter-spacing (-0.02em). Construction feel, highly legible.
- **Body:** `Inter`, system fallback — 400/500/600.
- **Mono/numbers:** `JetBrains Mono` or tabular-nums for stats, quote amounts.
- Scale: Hero 48/56, H2 32/40, H3 24/32, Body 16/24, Small 14/20.
- Import via Google Fonts in `globals.css`. Self-host for production.

## 4. Logo Idea

- **Mark:** Bold "B" formed by a steel beam + upward chevron / roofline. Orange square with slate cut.
- **Wordmark:** "Build**Track**" — Build in Slate-900, Track in Orange.
- **Clearspace:** Height of "B" on all sides. Min size 32px digital.
- **Favicon:** Orange rounded square, white BT beam mark.
- **Needed assets:** `logo.svg`, `logo-white.svg`, `favicon.svg`, `og-cover.jpg` (see `frontend/src/assets/README_ASSETS.md`).

## 5. Imagery

- Real site photos over stock. Hard hats, frames, concrete pours. Warm daylight.
- Overlay: `linear-gradient(rgba(26,36,48,.72), rgba(26,36,48,.35))` for hero legibility.
- No dark text on busy photos without overlay.

## 6. Components Style

- Buttons: 8px radius, 600 weight, uppercase? No — sentence case. `Get Free Quote`.
- Cards: white, 1px `#EAECF0` border, 12px radius, subtle shadow.
- Badges: orange-light bg + orange-dark text for "Licensed", "5.0 Rated", "On-Time".
- Stats: large tabular numbers (e.g., "120+"), small uppercase label.

## 7. Tone — Do / Don't

- Do: "Fixed quote in 48 hours. No hidden fees."
- Don't: "Best-in-class synergistic building solutions."
- Do: "See daily photos of your build."
- Don't: "Leverage cutting-edge paradigms."
