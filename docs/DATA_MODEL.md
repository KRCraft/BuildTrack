# BuildTrack — Data Model v1

> DB: PostgreSQL (prod) / SQLite (dev). ORM: Django.  
> This doc is the source of truth for entities, fields, and relations. Backend `backend/apps/*` models MUST match it. Frontend mirror: `frontend/src/utils/apiTypes.js`.

---

## 1. ER overview (text diagram)

```
                    ┌──────────┐
                    │   User   │ 1
                    └────┬─────┘
                         │ 1:1 (nullable, a client may exist without login and vice versa)
                    ┌────▼─────┐
                    │  Client  │ 1
                    └────┬─────┘
                         │ 1:N
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼─────┐    ┌─────▼──────┐   ┌─────▼──────────┐
   │ Project  │◄───│QuoteRequest│   │ ContactMessage │ (standalone, no FK)
   │          │ 1  │ (→Project  │   └────────────────┘
   │          │◄───┤ on accept, │
   └────┬─────┘ N  │ nullable)  │
        │ 1        └────────────┘
        │ N
   ┌────▼───────┐     ┌──────────┐
   │ Testimonial│ N:1 │ Milestone│ (nested under Project, optional MVP table)
   └────────────┘     └──────────┘

User 1:N QuoteRequest (optional `submitted_by` FK for authenticated submissions)
User 1:N Testimonial  (optional `author` FK)
```

Relation summary:

| From | To | Type | On delete | Notes |
|------|----|------|-----------|-------|
| Client → User | `user` | 1:1 nullable | SET_NULL | CRM record survives account deletion |
| Project → Client | `client` | N:1 nullable | SET_NULL | keep portfolio if client removed |
| QuoteRequest → User | `submitted_by` | N:1 nullable | SET_NULL | public quotes have null |
| QuoteRequest → Project | `converted_project` | 1:1 nullable | SET_NULL | set on accept+create |
| Testimonial → Project | `project` | N:1 nullable | SET_NULL | keep testimonial if project deleted |
| Testimonial → User | `author` | N:1 nullable | SET_NULL | |
| Milestone → Project | `project` | N:1 | CASCADE | milestones die with project |
| ContactMessage | — | standalone | — | no FKs by design (spam-safe) |

---

## 2. Tables

### 2.1 User (`users_user` — custom user, email as username)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL, indexed | login identifier |
| `password` | VARCHAR(128) | NOT NULL (hashed) | Django hashing |
| `full_name` | VARCHAR(150) | NOT NULL | display name |
| `phone` | VARCHAR(20) | NULL/blank | E.164 preferred |
| `company` | VARCHAR(150) | NULL/blank | |
| `role` | VARCHAR(20) | choices `admin\|client`, default `client` | coarse RBAC; `is_staff` mirrors `admin` |
| `is_staff` | BOOL | default False | Django admin access |
| `is_active` | BOOL | default True | soft-disable |
| `created_at` | TIMESTAMPTZ | auto_now_add | |
| `updated_at` | TIMESTAMPTZ | auto_now | |

Indexes: `email` unique. Choices enforced at model + serializer level.

### 2.2 Client (`clients_client`)

CRM record, admin-managed. May link to a `User`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `full_name` | VARCHAR(150) | NOT NULL | |
| `company` | VARCHAR(150) | NULL/blank | |
| `email` | EMAIL | NULL/blank, UNIQUE where not null | contact email |
| `phone` | VARCHAR(20) | NULL/blank, indexed | |
| `address` | TEXT | NULL/blank | |
| `user` | FK → User | NULL/blank, UNIQUE, SET_NULL | linked login |
| `notes` | TEXT | NULL/blank | internal, never public |
| `created_at` | TIMESTAMPTZ | auto_now_add | |
| `updated_at` | TIMESTAMPTZ | auto_now | |

Derived (annotated, not columns): `projects_count`, `active_quotes_count` (quotes with status in `new|contacted|estimated` matching email/phone).

### 2.3 Project (`projects_project`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `title` | VARCHAR(200) | NOT NULL | |
| `slug` | SLUG | UNIQUE, indexed | auto from title |
| `description` | TEXT | NOT NULL | |
| `client` | FK → Client | NULL, SET_NULL, indexed | owner |
| `status` | VARCHAR(20) | choices `planned\|in_progress\|on_hold\|completed\|cancelled`, default `planned`, indexed | workflow state |
| `progress` | SMALLINT | 0–100, default 0, validators | % complete |
| `budget` | DECIMAL(12,2) | NULL, >= 0 | |
| `currency` | CHAR(3) | default `USD` | ISO code |
| `start_date` | DATE | NULL | |
| `end_date` | DATE | NULL, must be >= start_date | validated |
| `location` | VARCHAR(255) | NULL/blank | |
| `cover_image` | IMAGE | NULL/blank, upload `projects/covers/` | |
| `gallery` | JSONB | default `[]` | list of image URLs/paths (MVP-simple vs M2M table) |
| `is_published` | BOOL | default True, indexed | public visibility gate |
| `is_featured` | BOOL | default False, indexed | homepage showcase |
| `tracking_code` | VARCHAR(20) | UNIQUE, indexed, auto `BT-YYYY-NNNN` | public tracking lookup |
| `created_at` | TIMESTAMPTZ | auto_now_add | |
| `updated_at` | TIMESTAMPTZ | auto_now | |

Business rules:
- `completed` requires `progress == 100` (serializer auto-sets 100 on transition, or rejects otherwise — pick one and document; recommended: auto-set).
- `cancelled` is terminal; no transitions out (reject in serializer).
- Public list queryset: `is_published=True`. Admin: all.
- `tracking_code` generated in `save()` if blank; never editable via API (read-only serializer field).

### 2.4 Milestone (`projects_milestone` — nested, optional but recommended)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `project` | FK → Project | CASCADE, related_name `milestones`, indexed | |
| `title` | VARCHAR(200) | NOT NULL | e.g. "Foundation" |
| `description` | TEXT | NULL/blank | |
| `due_date` | DATE | NULL | |
| `is_completed` | BOOL | default False | |
| `order` | SMALLINT | default 0 | display order |
| `created_at` | TIMESTAMPTZ | auto_now_add | |

Serialized nested read-only inside Project detail; separate CRUD only if needed (`/api/projects/:id/milestones/` read MVP).

### 2.5 QuoteRequest (`quotes_quoterequest`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `tracking_id` | VARCHAR(20) | UNIQUE, auto `Q-YYYY-NNNN`, indexed | customer-facing ref |
| `full_name` | VARCHAR(150) | NOT NULL | |
| `email` | EMAIL | NOT NULL, indexed | |
| `phone` | VARCHAR(20) | NOT NULL, indexed | |
| `service_type` | VARCHAR(20) | choices `construction\|renovation\|design\|consulting\|other`, default `other`, indexed | |
| `budget_range` | VARCHAR(20) | choices `under_10k\|10k_50k\|50k_100k\|over_100k\|undecided`, default `undecided` | lead qualification |
| `message` | TEXT | NOT NULL, min 10 | project description |
| `preferred_contact` | VARCHAR(20) | choices `phone\|email\|telegram\|whatsapp`, default `phone` | |
| `attachment_url` | URL | NULL/blank | MVP-simple (future: file table) |
| `status` | VARCHAR(20) | choices `new\|contacted\|estimated\|accepted\|declined\|expired`, default `new`, indexed | pipeline |
| `estimated_price` | DECIMAL(12,2) | NULL, >= 0 | set by admin |
| `admin_notes` | TEXT | NULL/blank, admin-only (excluded from client serializer) | |
| `submitted_by` | FK → User | NULL, SET_NULL | authenticated submitter |
| `converted_project` | OneToOne → Project | NULL, SET_NULL | set on accept+create |
| `created_at` | TIMESTAMPTZ | auto_now_add, indexed | SLA sorting |
| `updated_at` | TIMESTAMPTZ | auto_now | |

State machine (enforced in serializer/`clean()`):

```
new → contacted → estimated → accepted
                          ↘ declined
new → declined | expired (admin)
```

`estimated` should normally carry non-null `estimated_price` (warn, don't hard-fail — startup-flexible).

### 2.6 ContactMessage (`contact_contactmessage`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `name` | VARCHAR(150) | NOT NULL | |
| `email` | EMAIL | NOT NULL | |
| `phone` | VARCHAR(20) | NULL/blank | |
| `subject` | VARCHAR(200) | NOT NULL | |
| `message` | TEXT | NOT NULL, min 10 | |
| `is_read` | BOOL | default False, indexed | inbox filter |
| `reply_note` | TEXT | NULL/blank, admin-only | internal follow-up |
| `created_at` | TIMESTAMPTZ | auto_now_add | |

No FKs. Rate-limit public POST (5/hour/IP).

### 2.7 Testimonial (`testimonials_testimonial`)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | SERIAL PK | — | |
| `client_name` | VARCHAR(150) | NOT NULL | display name |
| `company` | VARCHAR(150) | NULL/blank | |
| `project` | FK → Project | NULL, SET_NULL | proof link |
| `rating` | SMALLINT | 1–5, NOT NULL, validators | |
| `text` | TEXT | NOT NULL, 20–1000 chars | |
| `avatar` | IMAGE | NULL/blank, upload `testimonials/avatars/` | |
| `author` | FK → User | NULL, SET_NULL | authenticated author |
| `is_approved` | BOOL | default False, indexed | public gate |
| `is_featured` | BOOL | default False | carousel pick |
| `created_at` | TIMESTAMPTZ | auto_now_add | |
| `updated_at` | TIMESTAMPTZ | auto_now | |

Public list queryset: `is_approved=True`. Submissions always create `is_approved=False` (even from staff via public endpoint — staff approves via PATCH).

---

## 3. Seed / fixture guidance (startup-appropriate)

- 1 admin (`admin@buildtrack.example.com`), 2 demo clients + users, 6 projects (3 featured, mixed statuses), 4 approved testimonials + 1 pending, 3 quotes in different pipeline stages, 2 unread contact messages.
- Use factories/fixtures so frontend can develop against realistic data on day one.

## 4. Migration order

1. `users` (no deps) → 2. `clients` (dep users) → 3. `projects` (dep clients) + milestones → 4. `quotes` (dep users, projects) → 5. `contact` (none) → 6. `testimonials` (dep projects, users).

## 5. Non-goals (explicitly excluded from v1 schema)

No payments, notifications, comments, file-attachments table, audit log, or multi-tenant orgs. `gallery` as JSONB and `attachment_url` as URL keep MVP lean; normalize later if needed.
