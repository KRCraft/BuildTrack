# BuildTrack — User Flows v1

> Personas: **Visitor** (anonymous), **Client** (registered), **Admin** (staff).  
> Related: `API_CONTRACT.md` (endpoints), `DATA_MODEL.md` (states). Frontend routes below are recommendations (`frontend/src/...`).

---

## A. Client journey (primary revenue path)

### A1. Visit → discover (Visitor)

1. Visitor lands on `/` (hero + featured projects + testimonials + CTA "Get a Quote").
2. Frontend: `GET /api/projects/featured/` → hero carousel; `GET /api/testimonials/?page_size=6` → social proof.
3. Visitor browses `/projects` (public list: `GET /api/projects/?search=&status=&ordering=-created_at`) and opens `/projects/:slug` (`GET /api/projects/:id/` with milestones/progress bar).
4. Trust builders: progress %, photos, testimonial linked via `project_title`, tracking code visible (`BT-2026-0012`).
5. Edge: unpublished projects never appear; direct URL to unpublished → `404` (not `403`, to avoid leaking existence).

### A2. Quote request (Visitor → Lead)

1. CTA → `/quote` form (fields: name, email, phone, service_type, budget_range, message, preferred_contact, optional attachment URL).
2. Submit → `POST /api/quotes/` (no login, rate-limited 5/hr/IP).
3. Success state: show `tracking_id` (`Q-2026-0021`) + "We reply within 24h via your preferred channel." Persist `tracking_id` in localStorage for later lookup UX.
4. Failures:
   - `400` validation → inline field errors from `errors{}`.
   - `429` → "You've sent several requests — we'll be in touch shortly." + contact fallback (`/contact`).
5. Optional: prompt "Create an account to track your quote" → `/register` (pre-fill email). If registered, future quotes link via `submitted_by`.

### A3. Register / login (Lead → Client)

1. `/register` → `POST /api/auth/register/` → auto-login (tokens stored in memory + refresh in httpOnly cookie or secure storage — frontend decision, document it).
2. `/login` → `POST /api/auth/login/` → redirect to `/dashboard` (client) or `/admin` (staff by `is_staff`).
3. Token refresh silent via `POST /api/auth/refresh/`.

### A4. Project tracking (Client)

1. Dashboard `/dashboard`: cards for own quotes (`GET /api/quotes/` — backend scopes to `submitted_by=request.user` or matching email) + own projects (backend scopes `project.client.user == request.user`; or lookup by `tracking_code` search for users without linked Client record).
2. Project detail `/tracking/:code`: progress bar (`progress`), status badge (`status_display`), timeline (milestones `title` + `is_completed` + `due_date`), budget/dates/location, gallery.
3. Statuses UX copy: `planned` "Scheduled", `in_progress` "Under construction", `on_hold` "Paused", `completed` "Delivered", `cancelled` "Cancelled".
4. Client cannot edit project (attempt → `403`). Client can submit new quote or contact message for change requests.

### A5. Testimonial (Client → Advocate)

1. After `completed`, dashboard shows "Share your experience" → `/testimonials/new`.
2. Submit → `POST /api/testimonials/` (linked `project`, `rating`, `text` ≥ 20 chars) → thanks state "Under review".
3. Once approved (`is_approved=true`), it appears in public carousel + project detail. Featured ones (`is_featured`) surface on homepage.

```
Visitor ──browse──▶ Quote ──register──▶ Client ──track──▶ Completed ──review──▶ Advocate
            │           │                  │                                │
     /projects    /quote (Q-xxx)      /dashboard                  /testimonials/new
```

---

## B. Admin journey (operations)

### B1. Triage quotes (daily)

1. Login → `/admin` → Quotes queue (`GET /api/quotes/?status=new&ordering=created_at` — oldest first for SLA).
2. Open `/admin/quotes/:id`: call/email client via `preferred_contact`, add `admin_notes` (`PATCH /api/quotes/:id/`).
3. Transition: `new → contacted` (after outreach), `contacted → estimated` (+ `estimated_price`), `estimated → accepted | declined`.
4. Accept path: `POST /api/quotes/:id/accept/?create_project=true` → creates `Project(status=planned, client=…)` → link shown (`project_id`). Decline/expire with note.
5. Invalid transition → `400`; UI disables illegal buttons per state machine (see DATA_MODEL §2.5).

### B2. Manage projects (weekly)

1. `/admin/projects`: table (`GET /api/projects/?all=true` with staff token to include unpublished), filter by `status`, search by title/tracking code.
2. Create: `/admin/projects/new` → `POST /api/projects/` (assign `client`, dates, budget, `is_published`, `is_featured`).
3. Update progress: inline slider → `PATCH /api/projects/:id/ { progress, status }`. Completing sets `progress=100` + `status=completed`.
4. Milestones: check off `is_completed` (nested update or future sub-endpoint).
5. Unpublish instead of delete (`is_published=false`); hard delete only for mistakes.

### B3. CRM + inbox (as needed)

1. Clients: `/admin/clients` — create/link `user`, view `projects_count`/`active_quotes_count`; delete blocked (`409`) if projects exist → reassign first.
2. Contact inbox: `/admin/inbox` (`GET /api/contact/?is_read=false`) → read → `PATCH { is_read:true, reply_note }`.
3. Testimonials moderation: `/admin/testimonials?is_approved=false` (or `/pending/`) → approve (`is_approved:true`) + optionally feature (`is_featured:true`); delete spam.

### B4. Content & trust loop

1. Feature best projects (`is_featured=true`, max ~6) → homepage updates automatically.
2. Feature 5-star testimonials → carousel.
3. Monthly: archive `completed` older than X, expire stale quotes (`status=expired`).

```
Admin:  login ──▶ triage quotes ──▶ accept ──▶ project created ──▶ update progress ──▶ completed
                          │                                              │                  │
                    /admin/quotes                              /admin/projects      ask testimonial
```

---

## C. Key edge cases & decisions

| # | Case | Decision |
|---|------|----------|
| 1 | Quote spam | rate limit + admin delete; no CAPTCHA in MVP (add hCaptcha later) |
| 2 | Client without linked `Client` CRM record | project lookup by `tracking_code` still works; admin links `user` later |
| 3 | Double submit (quote/contact/testimonial) | disable button on submit + idempotency via client-generated `Idempotency-Key` header (future); MVP: frontend guard only |
| 4 | 401 mid-session | silent refresh once, retry; else redirect `/login?next=...` |
| 5 | Unpublished/foreign project URL | `404` for anonymous; owner/admin get `200` |
| 6 | Quote edit after triage started | owner PATCH allowed only while `status==new`; else `403` with message |
| 7 | Testimonial with no project | allowed (`project=null`) — e.g. consulting clients |

## D. Route ↔ endpoint map (frontend checklist)

| Route | Endpoint(s) |
|-------|-------------|
| `/` | `GET /api/projects/featured/`, `GET /api/testimonials/?page_size=6` |
| `/projects`, `/projects/:slug` | `GET /api/projects/`, `GET /api/projects/:id/` |
| `/quote` | `POST /api/quotes/` |
| `/contact` | `POST /api/contact/` |
| `/register`, `/login`, `/profile` | `/api/auth/*` |
| `/dashboard`, `/tracking/:code` | `GET /api/quotes/`, `GET /api/projects/?search=:code` |
| `/testimonials/new` | `POST /api/testimonials/` |
| `/admin/*` | staff-scoped `GET/PATCH/POST/DELETE` per API_CONTRACT matrix |
