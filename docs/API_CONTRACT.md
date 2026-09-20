# BuildTrack — API Contract v1

> Base URL (dev): `http://localhost:8000/api/`  
> Base URL (prod): `https://api.buildtrack.example.com/api/`  
> API version: `v1` (unversioned prefix `/api/` for MVP; version via `Accept: application/json` + future `/api/v1/` alias)  
> Auth scheme: JWT Bearer (`Authorization: Bearer <access_token>`)  
> Content type: `application/json` (except noted)  
> Trailing slash: required by Django REST Framework (`/api/projects/` not `/api/projects`)  
> Date format: ISO-8601 UTC (`2026-09-12T10:00:00Z`)

This contract is frontend-binding. Backend MUST NOT break field names without a minor version bump. Frontend types in `frontend/src/utils/apiTypes.js` mirror this file.

---

## 1. Conventions

### 1.1 Roles

| Role | How determined | Capabilities |
|------|---------------|--------------|
| `public` | no token | list published projects/testimonials, create quote/contact/testimonial, register/login |
| `client` | `user.role == "client"` | + list own quotes, retrieve own projects, update profile |
| `admin`/`staff` | `user.is_staff == true` or `role == "admin"` | full CRUD on all resources, status transitions, approvals |

### 1.2 Common envelope

List responses (paginated, DRF default):

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/projects/?page=2",
  "previous": null,
  "results": [ { "...": "..." } ]
}
```

Query params supported on all list endpoints:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | page number |
| `page_size` | int | 12 (max 100) | items per page |
| `search` | string | — | full-text search (endpoint-specific fields) |
| `ordering` | string | `-created_at` | e.g. `?ordering=budget` or `?ordering=-created_at` |

### 1.3 Error envelope

```json
{
  "detail": "Human readable message.",
  "code": "not_found",
  "errors": {
    "email": ["This field is required."]
  }
}
```

Status codes used: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `429 Too Many Requests`.

### 1.4 Auth header

```
Authorization: Bearer eyJhbGciOi...
```

Access token lifetime: 60 min. Refresh lifetime: 7 days.

---

## 2. Auth — `/api/auth/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | public | Register new client user |
| POST | `/api/auth/login/` | public | Obtain JWT pair |
| POST | `/api/auth/refresh/` | public (refresh token) | Refresh access token |
| POST | `/api/auth/logout/` | authenticated | Blacklist refresh token (optional MVP) |
| GET | `/api/auth/me/` | authenticated | Current user profile |
| PATCH | `/api/auth/me/` | authenticated | Update profile (name, phone, company) |
| POST | `/api/auth/password/change/` | authenticated | Change password |

### POST `/api/auth/register/`

Request:

```json
{
  "email": "client@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "full_name": "Amina Karimova",
  "phone": "+998901234567",
  "company": "Karimov Stroy"
}
```

Validation: `email` unique, `password` min 8 chars, must match `password_confirm`.

Response `201`:

```json
{
  "id": 7,
  "email": "client@example.com",
  "full_name": "Amina Karimova",
  "phone": "+998901234567",
  "company": "Karimov Stroy",
  "role": "client",
  "is_staff": false,
  "created_at": "2026-09-12T10:00:00Z",
  "tokens": {
    "access": "<jwt>",
    "refresh": "<jwt>"
  }
}
```

Errors `400`: `{ "errors": { "email": ["User with this email already exists."] } }`

### POST `/api/auth/login/`

Request:

```json
{ "email": "client@example.com", "password": "SecurePass123!" }
```

Response `200`:

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": {
    "id": 7,
    "email": "client@example.com",
    "full_name": "Amina Karimova",
    "role": "client",
    "is_staff": false
  }
}
```

Error `401`: `{ "detail": "Invalid credentials.", "code": "auth_failed" }`

### POST `/api/auth/refresh/`

Request: `{ "refresh": "<jwt>" }` → Response `200`: `{ "access": "<new_jwt>" }`

### GET `/api/auth/me/`

Response `200`:

```json
{
  "id": 7,
  "email": "client@example.com",
  "full_name": "Amina Karimova",
  "phone": "+998901234567",
  "company": "Karimov Stroy",
  "role": "client",
  "is_staff": false,
  "created_at": "2026-09-12T10:00:00Z",
  "updated_at": "2026-09-12T10:00:00Z"
}
```

### PATCH `/api/auth/me/`

Updatable: `full_name`, `phone`, `company`. Response `200` = updated user object.

### POST `/api/auth/password/change/`

Request: `{ "old_password": "...", "new_password": "...", "new_password_confirm": "..." }` → `200`: `{ "detail": "Password updated." }`

---

## 3. Projects — `/api/projects/`

Public portfolio + client project tracking. Core BuildTrack resource.

Project statuses: `planned` → `in_progress` → `on_hold` → `in_progress` → `completed` (+ `cancelled` terminal). Progress 0–100.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/projects/` | public | List projects (public sees only `is_published=true`; admin sees all via `?all=true` or staff token) |
| POST | `/api/projects/` | admin | Create project |
| GET | `/api/projects/:id/` | public (published) / client-owner / admin | Retrieve detail incl. milestones |
| PUT/PATCH | `/api/projects/:id/` | admin | Full/partial update (status, progress) |
| DELETE | `/api/projects/:id/` | admin | Delete (or archive via `is_published=false` preferred) |
| GET | `/api/projects/:id/milestones/` | auth per project visibility | List milestones (nested) |
| GET | `/api/projects/featured/` | public | Featured projects (`is_featured=true`, published, max 6) |

List filters: `?status=in_progress&client=3&is_featured=true&search=villa&ordering=-created_at`

### Project object

```json
{
  "id": 12,
  "title": "Tashkent Villa — Yunusabad",
  "slug": "tashkent-villa-yunusabad",
  "description": "240 m² two-storey villa, turnkey.",
  "client": 4,
  "client_name": "Karimov Stroy",
  "status": "in_progress",
  "status_display": "In Progress",
  "progress": 65,
  "budget": "85000.00",
  "currency": "USD",
  "start_date": "2026-06-01",
  "end_date": "2026-12-15",
  "location": "Tashkent, Yunusabad",
  "cover_image": "http://localhost:8000/media/projects/covers/villa.jpg",
  "gallery": ["http://localhost:8000/media/projects/gallery/1.jpg"],
  "is_published": true,
  "is_featured": true,
  "tracking_code": "BT-2026-0012",
  "created_at": "2026-06-01T08:00:00Z",
  "updated_at": "2026-09-10T14:00:00Z",
  "milestones": [
    { "id": 1, "title": "Foundation", "is_completed": true, "due_date": "2026-07-01" }
  ]
}
```

Field rules:
- `title`: required, max 200
- `slug`: auto-generated, unique, read-only on create (editable by admin)
- `status`: enum `planned|in_progress|on_hold|completed|cancelled`
- `progress`: int 0–100
- `budget`: decimal string, >= 0
- `tracking_code`: read-only, format `BT-YYYY-NNNN`, used for public tracking lookup `?search=BT-2026-0012`
- `cover_image`/`gallery`: multipart upload OR URL; on JSON create accept URL strings

### POST `/api/projects/` (admin)

Request (JSON):

```json
{
  "title": "Office Renovation — IT Park",
  "description": "450 m² office fit-out.",
  "client": 4,
  "status": "planned",
  "progress": 0,
  "budget": "42000.00",
  "currency": "USD",
  "start_date": "2026-10-01",
  "end_date": "2027-01-30",
  "location": "Tashkent, IT Park",
  "is_published": true,
  "is_featured": false
}
```

Response `201`: full Project object. `403` for non-staff.

### PATCH `/api/projects/:id/` (admin) — progress update

```json
{ "progress": 70, "status": "in_progress" }
```

Backend validates: cannot set `completed` unless `progress == 100` (or backend auto-sets 100). Frontend should enforce same.

---

## 4. Clients — `/api/clients/`

Admin-only CRM. Public never sees this endpoint (public client names come denormalized via `project.client_name`).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/clients/` | admin | List clients |
| POST | `/api/clients/` | admin | Create client |
| GET | `/api/clients/:id/` | admin | Retrieve + nested projects/quotes summary |
| PUT/PATCH | `/api/clients/:id/` | admin | Update |
| DELETE | `/api/clients/:id/` | admin | Delete (blocked `409` if projects exist) |

Filters: `?search=karimov&ordering=-created_at`

### Client object

```json
{
  "id": 4,
  "full_name": "Amina Karimova",
  "company": "Karimov Stroy",
  "email": "client@example.com",
  "phone": "+998901234567",
  "address": "Tashkent, Amir Temur 15",
  "user": 7,
  "notes": "Prefers Telegram contact.",
  "projects_count": 2,
  "active_quotes_count": 1,
  "created_at": "2026-05-01T09:00:00Z",
  "updated_at": "2026-09-01T09:00:00Z"
}
```

- `user`: nullable FK → User (links login account to CRM record; one-to-one-ish)
- `email`: unique if present
- DELETE with existing projects → `409 { "detail": "Cannot delete client with existing projects." }`

---

## 5. Quotes / Quote Requests — `/api/quotes/`

Lead capture + estimation pipeline. Highest startup value — keep friction low for public creation.

Statuses: `new` → `contacted` → `estimated` → `accepted` | `declined` (+ `expired`).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/quotes/` | client (own) / admin (all) | List. Client sees `?mine=true` implicit; admin may filter `?status=new` |
| POST | `/api/quotes/` | public (rate-limited) | Submit quote request |
| GET | `/api/quotes/:id/` | owner / admin | Retrieve |
| PATCH | `/api/quotes/:id/` | owner (limited) / admin (full) | Owner may edit only while `status==new`; admin may transition status + set `estimated_price` |
| DELETE | `/api/quotes/:id/` | admin | Delete spam |
| POST | `/api/quotes/:id/accept/` | admin or owner | Mark accepted (creates Project optionally — see below) |

Filters: `?status=new&service_type=construction&search=+99890`

### POST `/api/quotes/` (public — no token required)

Request:

```json
{
  "full_name": "Otabek Nazarov",
  "email": "otabek@example.com",
  "phone": "+998909876543",
  "service_type": "renovation",
  "budget_range": "10k_50k",
  "message": "Need 120 m² apartment renovation in Sergeli.",
  "preferred_contact": "telegram",
  "attachment_url": "https://.../floorplan.pdf"
}
```

Enums:
- `service_type`: `construction|renovation|design|consulting|other`
- `budget_range`: `under_10k|10k_50k|50k_100k|over_100k|undecided`
- `preferred_contact`: `phone|email|telegram|whatsapp`

Response `201`:

```json
{
  "id": 21,
  "tracking_id": "Q-2026-0021",
  "full_name": "Otabek Nazarov",
  "email": "otabek@example.com",
  "phone": "+998909876543",
  "service_type": "renovation",
  "budget_range": "10k_50k",
  "message": "Need 120 m² apartment renovation in Sergeli.",
  "preferred_contact": "telegram",
  "status": "new",
  "estimated_price": null,
  "admin_notes": null,
  "created_at": "2026-09-12T10:00:00Z"
}
```

Rate limit: 5/hour per IP → `429 { "detail": "Too many quote requests. Try again later." }`. Honeypot/spam check optional.

### PATCH `/api/quotes/:id/` (admin status transition)

```json
{ "status": "estimated", "estimated_price": "18500.00", "admin_notes": "Includes materials." }
```

Allowed transitions enforced (invalid → `400 { "errors": { "status": ["Cannot transition from accepted to new."] } }`).

### POST `/api/quotes/:id/accept/` (admin)

Optional `?create_project=true` → backend creates linked `Project` (`status=planned`) and returns:

```json
{ "quote": { "...": "...", "status": "accepted" }, "project_id": 13 }
```

---

## 6. Contact Messages — `/api/contact/`

Simple inbound mailbox.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/contact/` | public | Submit message |
| GET | `/api/contact/` | admin | List (filter `?is_read=false`) |
| GET | `/api/contact/:id/` | admin | Retrieve |
| PATCH | `/api/contact/:id/` | admin | Mark read / add reply note |
| DELETE | `/api/contact/:id/` | admin | Delete |

### POST `/api/contact/`

Request:

```json
{ "name": "Dilnoza", "email": "dilnoza@example.com", "phone": "+998901111111", "subject": "Partnership", "message": "We supply cement. Interested in partnership?" }
```

Response `201`:

```json
{ "id": 9, "name": "Dilnoza", "email": "dilnoza@example.com", "subject": "Partnership", "message": "...", "is_read": false, "created_at": "2026-09-12T10:00:00Z" }
```

### PATCH `/api/contact/:id/` (admin)

```json
{ "is_read": true, "reply_note": "Replied via email 12.09." }
```

---

## 7. Testimonials — `/api/testimonials/`

Social proof. Public reads approved only; submission open; approval gated.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/testimonials/` | public | List **approved only** (`is_approved=true`) |
| POST | `/api/testimonials/` | public/authenticated | Submit testimonial (authenticated pre-fills name; sets `is_approved=false`) |
| GET | `/api/testimonials/:id/` | public (approved) / admin (any) | Retrieve |
| PATCH | `/api/testimonials/:id/` | admin | Approve/edit/feature |
| DELETE | `/api/testimonials/:id/` | admin | Delete |
| GET | `/api/testimonials/pending/` | admin | Shortcut list `is_approved=false` (or `?is_approved=false`) |

### Testimonial object

```json
{
  "id": 5,
  "client_name": "Jasur Aliyev",
  "company": "Aliyev Group",
  "project": 12,
  "project_title": "Tashkent Villa — Yunusabad",
  "rating": 5,
  "text": "BuildTrack delivered two weeks early. Transparent tracking was excellent.",
  "avatar": "http://localhost:8000/media/testimonials/avatars/jasur.jpg",
  "is_approved": true,
  "is_featured": true,
  "created_at": "2026-08-20T12:00:00Z"
}
```

- `rating`: int 1–5, required
- `text`: required, min 20 chars, max 1000
- `project`: nullable FK (link to showcase real work)
- POST public request: `{ "client_name": "...", "company": "...", "rating": 5, "text": "...", "project": 12 }` → `201` with `is_approved: false` + `{ "detail": "Thanks! Your testimonial is under review." }` (detail in wrapper or second field — frontend: show thanks state)
- Admin approve: `PATCH { "is_approved": true, "is_featured": true }`

---

## 8. Frontend integration notes

1. **Axios base**: `const api = axios.create({ baseURL: "/api/", headers: {...} })`; attach Bearer via interceptor; refresh on 401 once then retry.
2. **Public quote form** posts to `/api/quotes/` with no token — handle `429` with friendly cooldown message.
3. **Project tracking page**: `GET /api/projects/?search=<tracking_code>` — single-result UX; if `count==1` auto-open detail.
4. **Testimonials carousel**: `GET /api/testimonials/?page_size=6&ordering=-created_at` (backend already filters approved for anonymous).
5. **Admin tables**: pass staff token; filter `?status=` + `?search=`; use `PATCH` for inline status edits.
6. **Media**: prefer `FormData` for `cover_image` upload: `Content-Type: multipart/form-data`; backend also accepts URL strings.
7. **All mutation helpers** live in `frontend/src/utils/api.js`; **types** in `frontend/src/utils/apiTypes.js` (this contract's mirror).

---

## 9. Future (out of MVP scope, do not implement yet)

- `/api/projects/:id/updates/` (timeline posts), `/api/notifications/`, `/api/payments/`
- WebSocket project progress push
- `POST /api/quotes/:id/attachments/` multi-file upload

---

## Appendix A — Quick method matrix

```
POST   /api/auth/register/          public
POST   /api/auth/login/             public
POST   /api/auth/refresh/           public
GET    /api/auth/me/                auth
PATCH  /api/auth/me/                auth

GET    /api/projects/               public (published)
POST   /api/projects/               admin
GET    /api/projects/:id/           public/admin
PATCH  /api/projects/:id/           admin
DELETE /api/projects/:id/           admin

GET    /api/clients/                admin
POST   /api/clients/                admin
GET    /api/clients/:id/            admin
PATCH  /api/clients/:id/            admin
DELETE /api/clients/:id/            admin

GET    /api/quotes/                 client/admin
POST   /api/quotes/                 public
GET    /api/quotes/:id/             owner/admin
PATCH  /api/quotes/:id/             owner(limited)/admin
DELETE /api/quotes/:id/             admin

POST   /api/contact/                public
GET    /api/contact/                admin
GET    /api/contact/:id/            admin
PATCH  /api/contact/:id/            admin

GET    /api/testimonials/           public (approved)
POST   /api/testimonials/           public
GET    /api/testimonials/:id/       public/admin
PATCH  /api/testimonials/:id/       admin
DELETE /api/testimonials/:id/       admin
```
