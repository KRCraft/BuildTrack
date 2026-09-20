# BuildTrack Assets — What to Add

Place files under `frontend/src/assets/` (bundled) or `frontend/public/images/` (static).
Current code uses `/images/projects/*.jpg` paths — add real photos to `frontend/public/images/projects/`.

## Required

| File | Size / Format | Notes |
|---|---|---|
| `logo.svg` | vector, 180×48 | Orange beam-B + "BuildTrack" (slate/orange). Transparent bg |
| `logo-white.svg` | vector | White version for dark header/footer |
| `favicon.svg` | 64×64 | Orange rounded square, white BT mark |
| `og-cover.jpg` | 1200×630 | Hero site photo + overlay + headline for social share |
| `hero-site.jpg` | 1920×1080, <300KB webp/jpg | Daylight framing/concrete pour, no text baked in |
| `images/projects/*.jpg` | 1200×800, <200KB each | `maple-home`, `cafe-fitout`, `oak-renovation`, `lakeside-duplex`, `clinic-refurb`, `cedar-kitchen` |
| `images/team/*.jpg` | 800×800 | 3 portraits: founder, site manager, designer |
| `icons/` | svg | Keep emoji placeholders until custom icons done |

## Guidelines

- Prefer `.webp` with `.jpg` fallback. Lazy-load below fold.
- Alt text mandatory. No text baked into photos (overlay in CSS).
- License: use only owned/client-consented photos. No unlicensed stock in production.
- Optimize: `npx sharp` or squoosh, max 2000px longest edge.
