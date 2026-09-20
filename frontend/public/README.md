# BuildTrack `frontend/public/`

Static files served at `/`. Merge-safe — Agent 4 only adds docs/placeholders, no build config changes.

## Structure

```
public/
  favicon.svg        → TODO: add (see src/assets/README_ASSETS.md)
  og-cover.jpg       → TODO: social share image 1200×630
  images/projects/   → TODO: 6 project photos (maple-home, cafe-fitout, oak-renovation, lakeside-duplex, clinic-refurb, cedar-kitchen)
  robots.txt         → TODO: allow /, sitemap reference
  manifest.json      → TODO: PWA name/icons if needed
```

## Conventions

- Paths referenced as `/images/...` map here.
- Don't commit >500KB images — optimize first.
- `index.html` / `vite.config` owned by Agent 2 — do not edit here.
