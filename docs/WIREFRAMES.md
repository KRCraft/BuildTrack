# BuildTrack Wireframes (Text)

Landing + core pages. Mobile-first. All CTAs point to `/quote` with label "Get Free Quote".

## 1. Home (`/`)

```
[Header: logo | Home Services Projects About Contact | (555) 123-4567 | Get Free Quote btn]
[Hero: bg site photo + slate overlay]
  Badge: "Licensed • Insured • 4.9★ from 200+ reviews"
  H1: "Your Dream Build, Delivered On Time and On Budget."
  Sub: "Custom homes, renovations & commercial fit-outs with fixed quotes and live progress tracking."
  [Get Free Quote] [View Our Work]
  Trust row: 120+ Projects | 15 Yrs | 98% On-Time | $45M Built
[StatsBar: 4 stats strip on slate]
[Services grid: 6 cards w/ icon, title, 1-line, Learn more]
[Why Us: photo left, checklist right + CTA]
[Featured Projects: 3 cards w/ image, location, type, cost range]
[Testimonials carousel: 3 visible, stars, quote, name]
[CTASection: orange bg — "Ready to start? Get your free fixed quote in 48 hours." + button + phone]
[Footer: columns Services/Company/Contact + license # + hours]
```

## 2. Services (`/services`)

```
[Page hero: H1 "What We Build" + sub]
[ServicesDetail: alternating rows — image | title, bullets, price-from, CTA]
  1. Custom Homes — from $280k
  2. Renovations & Extensions — from $45k
  3. Commercial Fit-Outs — custom
  4. Roofing & Cladding — from $12k
  5. Kitchens & Baths — from $18k
  6. Project Management / Tracking — included free
[Process: 4 steps — Site Visit > Fixed Quote > Build + Daily Photos > Handover + Warranty]
[CTASection reuse]
```

## 3. Projects (`/projects`)

```
[Page hero + filter chips: All / Homes / Renovations / Commercial]
[Grid 3-col: card = image, status badge (Completed/In Progress), title, location, specs (sqft, duration, value)]
[Click → detail: gallery, scope list, timeline, testimonial]
[StatsBar reuse: proves volume]
[CTASection: "Have a project like this? Get Free Quote"]
```

## 4. Quote (`/quote`)

```
[Split layout]
Left (slate bg): "Get Your Free Quote in 48 Hours" + bullets (No obligation, Fixed price, Licensed builder calls you) + phone + testimonials mini
Right (form card): Name, Phone, Email, Service [select], Budget [select], Location, Message, Preferred contact, [Request My Free Quote]
Success state: check icon + "Thanks {name}! We'll call within 1 business day." + ref #
Trust footer: license, insurance, privacy note
```

## 5. Global Notes

- Header sticky, shrinks on scroll. Mobile hamburger.
- All images lazy-load, alt text required.
- Forms: inline validation, honeypot + rate-limit (backend).
- Analytics events: `cta_quote_click`, `form_quote_submit`, `project_view`.
