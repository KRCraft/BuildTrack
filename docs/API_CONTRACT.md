# BuildTrack — API Contract v1.1

> Base URL (dev): `http://localhost:8000/api/v1/`  
> Base URL (prod): `https://api.buildtrack.example.com/api/v1/`  
> Version: `v1` via path `/api/v1/` (live, all endpoints versioned)  
> Auth: JWT Bearer `Authorization: Bearer <access>` + tenant header `X-Company-ID: <uuid>`  
> Refresh: HttpOnly cookie `buildtrack_refresh` at `POST /api/v1/auth/refresh/` (SameSite=Lax, Secure in prod, `credentials:include`)  
> Content type: `application/json` (except file uploads)  
> Trailing slash: required (`/api/v1/projects/` not `/api/v1/projects`)  
> Date: ISO-8601 `YYYY-MM-DD` for dates, UTC `2026-09-20T10:00:00Z` for timestamps  
> Pagination: DRF PageNumberPagination `PAGE_SIZE=25` (max 100 via `page_size` if added)

This contract is frontend-binding (`frontend/lib/api.ts`, `frontend/src/utils/apiTypes.js` legacy). Breaking field names requires minor version bump. Live backend: `backend/config/urls.py` + `backend/apps/*/urls.py`.

---

## 1. Conventions

### 1.1 Roles (CompanyMembership.Role)

| Role | Capabilities |
|------|--------------|
| `OWNER` | Full company, approve budgets/expenses/reports, manage members/materials/locations, view audit logs |
| `PROJECT_MANAGER` | Create/manage projects, create budgets/reports/expenses (if assigned), dispatch transfers |
| `SITE_MANAGER` | Receive transfers, record usage, limited project scope |
| `ACCOUNTANT` | View balances/transactions, approve expenses, view financials |
| `VIEWER` | Read-only (assigned projects only) |

OWNER/ACCOUNTANT see all company projects; others only via `ProjectAssignment` (`company_projects()` helper).

### 1.2 Tenant header

All domain endpoints require `X-Company-ID: <uuid>` where `uuid` is a `Company.id` the user is `ACTIVE` member of. Missing/inactive → `404` (via `request_company()`). Frontend sends via `frontend/lib/api.ts` `getCompanyId()` from `localStorage.buildtrack_company`.

### 1.3 Common envelope

Paginated list:

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/expenses/?page=2",
  "previous": null,
  "results": [ { "...": "..." } ]
}
```

Not all lists are paginated yet — `projects, materials, locations, transfers, reports` currently return bare arrays (`200 [ ... ]`); `expenses, transactions, audit-logs` are paginated. Standardize to paginated in v1.2.

Query params (endpoint-specific): `page`, `search`, `status`, `project`, `material`, `location`, `date_from`, `date_to`.

### 1.4 Error envelope

```json
{
  "detail": "Human readable",
  "code": "not_found",
  "errors": { "email": ["This field is required."] }
}
```

### 1.5 Auth headers

```
Authorization: Bearer <access>   (15min)
X-Company-ID: <company-uuid>
Cookie: buildtrack_refresh=<refresh>  (7d, HttpOnly, Path=/api/v1/auth/)
```

Refresh flow: `401` → `POST /api/v1/auth/refresh/` with `credentials:include` → new `access` (and rotated `refresh` cookie if `ROTATE_REFRESH_TOKENS=True`).

### 1.6 Rate limiting

`REST_FRAMEWORK.DEFAULT_THROTTLE_RATES: anon 100/hour, user 1000/hour, login 10/minute`. Public `register/login` throttled; quote/contact legacy 5/hour **not yet implemented** (future via `DEFAULT_THROTTLE_RATES` `quotes`).

---

## 2. Auth — `/api/v1/auth/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register/` | AllowAny | Register `{email, first_name, last_name, password}` → 201 + `{access, refresh}` + Set-Cookie |
| POST | `/api/v1/auth/login/` | AllowAny | `{email, password}` → 200 `{access, refresh}` + Set-Cookie + `{user}` |
| POST | `/api/v1/auth/refresh/` | cookie | Uses `buildtrack_refresh` cookie → 200 `{access}` + rotated cookie |
| POST | `/api/v1/auth/logout/` | authenticated | Blacklist refresh, delete cookie |
| GET | `/api/v1/auth/me/` | authenticated | Current user profile |
| POST | `/api/v1/auth/password/reset/` | AllowAny | `{email}` → 200 (console email `uid, token`) |
| POST | `/api/v1/auth/password/reset/confirm/` | AllowAny | `{uid, token, new_password}` → 200 |

### POST `/api/v1/auth/register/`

Request:

```json
{ "email": "owner@example.com", "first_name": "Amina", "last_name": "Karimova", "password": "SecurePass123!" }
```

Response `201`:

```json
{
  "id": "uuid",
  "email": "owner@example.com",
  "first_name": "Amina",
  "last_name": "Karimova",
  "tokens": { "access": "<jwt>", "refresh": "<jwt>" }
}
```

Also `Set-Cookie: buildtrack_refresh=<refresh>; HttpOnly; Path=/api/v1/auth/; SameSite=Lax; Max-Age=604800`.

Errors `400`: `{ "errors": { "email": ["User with this email already exists."] } }`

### POST `/api/v1/auth/login/`

Request `{ "email": "...", "password": "..." }` → `200 { "access": "...", "refresh": "...", "user": { "id", "email", "first_name", "last_name" } }` + Set-Cookie. `401` invalid.

### POST `/api/v1/auth/refresh/`

No body (cookie). `200 { "access": "<new>" }` + `Set-Cookie` rotated. `401` if missing/invalid/blacklisted.

---

## 3. Companies — `/api/v1/companies/`

| Method | Endpoint | Auth | Role |
|--------|----------|------|------|
| GET | `/api/v1/companies/` | auth | any member — lists `is_active` companies where `status=ACTIVE` |
| POST | `/api/v1/companies/` | auth | any — creates Company + OWNER Membership for caller |
| GET | `/api/v1/companies/<uuid>/` | auth + X-Company-ID | member |
| POST | `/api/v1/companies/<uuid>/invitations/` | auth + X-Company-ID | OWNER — `{email, role}` → creates invitation, revokes prior PENDING, sends email |
| POST | `/api/v1/companies/invitations/accept/` | auth | any — `{token}` (raw secrets.token_urlsafe) → `update_or_create` Membership, `select_for_update` + expiry + email match |

Company object:

```json
{
  "id": "uuid",
  "name": "Karimov Stroy",
  "slug": "karimov-stroy",
  "currency_code": "UZS",
  "timezone": "Asia/Tashkent",
  "is_active": true,
  "created_at": "2026-09-20T10:00:00Z"
}
```

Errors: `409` duplicate slug → `slug-2`, `403` non-OWNER invites OWNER (allowed in code — privilege note).

---

## 4. Projects — `/api/v1/projects/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/projects/` | auth + X-Company-ID | List via `company_projects()`; filters `?status=&search=` (search `name|code|client_name` via `|` queryset — recommend `Q` + `distinct`) |
| POST | `/api/v1/projects/` | auth + X-Company-ID | OWNER/PROJECT_MANAGER only |
| GET | `/api/v1/projects/<uuid>/` | auth + X-Company-ID | via `project_or_404` (membership scoped) |
| PATCH | `/api/v1/projects/<uuid>/` | auth + X-Company-ID | `can_manage_project` (OWNER or PM assignment) |
| POST | `/api/v1/projects/<uuid>/archive/` | auth + X-Company-ID | `can_manage_project`, sets `status=ARCHIVED, is_archived=True` |
| GET | `/api/v1/projects/<uuid>/assignments/` | auth + X-Company-ID | List assignments |
| POST | `/api/v1/projects/<uuid>/assignments/` | auth + X-Company-ID | `can_manage_project`, validates `role` allowed (OWNER→any, PM→PM/VIEWER) |

Project statuses: `DRAFT, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED`. No `planned/in_progress` (legacy docs) — live is `DRAFT/ACTIVE`.

Project object (serializer):

```json
{
  "id": "uuid",
  "company": "uuid",
  "code": "BT-2026-001",
  "name": "Tashkent Villa — Yunusabad",
  "client_name": "Karimov Stroy",
  "status": "ACTIVE",
  "progress_percent_cache": "0.00",
  "budget_planned": "85000.00",
  "is_archived": false,
  "version": 1,
  "created_at": "2026-09-20T10:00:00Z",
  "updated_at": "2026-09-20T10:00:00Z"
}
```

List is **not yet paginated** — returns `200 [ ... ]` (should be `{count, results}`).

---

## 5. Budgets — `/api/v1/projects/<uuid>/budget/` + `/api/v1/budget-versions/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/projects/<uuid>/budget/` | auth + X-Company-ID | `200 Budget` or `404` if none (fixed from `200 null`) |
| POST | `/api/v1/projects/<uuid>/budget/` | auth + X-Company-ID | OWNER/PM — creates `Budget` + `BudgetVersion v1 DRAFT` → 201 |
| POST | `/api/v1/projects/<uuid>/budget/revisions/` | auth + X-Company-ID | creates new `BudgetVersion` via `create_revision()` (copies `lineage_key`) |
| GET | `/api/v1/budget-versions/<uuid>/` | auth + X-Company-ID | Retrieve |
| PATCH | `/api/v1/budget-versions/<uuid>/` | auth + X-Company-ID | `editable` (DRAFT + `can_manage_project`), bumps `version` |
| POST | `/api/v1/budget-versions/<uuid>/submit/` | auth + X-Company-ID | `refresh_total()`, `DRAFT→PENDING_APPROVAL` |
| POST | `/api/v1/budget-versions/<uuid>/approve/` | auth + X-Company-ID | **OWNER only** (note: expenses allow OWNER/ACCOUNTANT, inconsistency) |
| POST | `/api/v1/budget-versions/<uuid>/reject/` | auth + X-Company-ID | OWNER only, must be PENDING_APPROVAL |
| POST | `/api/v1/budget-versions/<uuid>/categories/` | auth + X-Company-ID | Create `BudgetCategory` |
| PATCH | `/api/v1/budget-categories/<uuid>/` | auth + X-Company-ID | Edit if version DRAFT |
| DELETE | `/api/v1/budget-categories/<uuid>/` | auth + X-Company-ID | Block if `children.exists()` |

BudgetVersion statuses: `DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, SUPERSEDED`.

---

## 6. Expenses — `/api/v1/expenses/` + `/api/v1/suppliers/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/suppliers/` | auth + X-Company-ID | List |
| POST | `/api/v1/suppliers/` | auth + X-Company-ID | OWNER/ACCOUNTANT only |
| GET/PATCH | `/api/v1/suppliers/<uuid>/` | auth + X-Company-ID | OWNER/ACCOUNTANT patch |
| GET | `/api/v1/expenses/?project_id=&status=&category=&supplier=&date_from=&date_to=&page=1` | auth + X-Company-ID | **Paginated** (`PageNumberPagination` 25) |
| POST | `/api/v1/expenses/` | auth + X-Company-ID | `Idempotency-Key: <uuid>` header supported → 200 existing vs 201 new; validates `category.company==company`, `category.version==project.budget.active_version`, `currency==company.currency_code` |
| GET/PATCH | `/api/v1/expenses/<uuid>/` | auth + X-Company-ID | PATCH only `DRAFT+STANDARD` + `may_create_expense()` |
| POST | `/api/v1/expenses/<uuid>/submit/` | auth + X-Company-ID | `DRAFT→PENDING_APPROVAL` |
| POST | `/api/v1/expenses/<uuid>/approve/` | auth + X-Company-ID | **OWNER/ACCOUNTANT** (diff from budgets OWNER-only) |
| POST | `/api/v1/expenses/<uuid>/reject/` | auth + X-Company-ID | OWNER/ACCOUNTANT |
| POST | `/api/v1/expenses/<uuid>/reverse/` | auth + X-Company-ID | Creates `REVERSAL` expense, `DRAFT`, same `correction_group_id` |
| POST | `/api/v1/expenses/<uuid>/attachments/` | auth + X-Company-ID | `multipart/form-data` `file` (PDF/JPG/PNG 10MB) |

Expense object (key fields):

```json
{
  "id": "uuid",
  "project": "uuid",
  "budget_category": "uuid",
  "supplier": "uuid",
  "amount": "1200.00",
  "currency_code": "UZS",
  "expense_date": "2026-09-20",
  "status": "DRAFT",
  "expense_type": "STANDARD",
  "idempotency_key": "uuid",
  "correction_group_id": "uuid",
  "version": 1
}
```

Filters: `project_id` (FK id, fixed from `project` string bug), `status`, `category` (=`budget_category`), `supplier`.

---

## 7. Inventory — `/api/v1/materials/` + `/api/v1/inventory/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/materials/?search=&category=` | auth + X-Company-ID | List materials (bare array, not paginated) |
| POST | `/api/v1/materials/` | auth + X-Company-ID | OWNER only |
| GET/PATCH | `/api/v1/materials/<uuid>/` | auth + X-Company-ID | OWNER patch |
| GET | `/api/v1/inventory/locations/` | auth + X-Company-ID | `project__in=company_projects` OR `project=None` |
| POST | `/api/v1/inventory/locations/` | auth + X-Company-ID | OWNER only |
| GET/PATCH | `/api/v1/inventory/locations/<uuid>/` | auth + X-Company-ID | `location_or_404` + project check |
| GET | `/api/v1/inventory/balances/?project=&material=&location=&low_stock=` | auth + X-Company-ID | Returns `[{id, material, location, quantity_on_hand, minimum_stock_level, low_stock: bool}]` (`low_stock` bool fixed from string, total computed via `mat_totals`) |
| GET | `/api/v1/inventory/transactions/?material=&location=&project=&transaction_type=&date_from=&date_to=&page=1` | auth + X-Company-ID | **Paginated** 25, OWNER/ACCOUNTANT see all, others filtered `project__in=company_projects` |
| POST | `/api/v1/inventory/receipt/` | auth + X-Company-ID | `Idempotency-Key`, `inventory_operator` check (OWNER or PM/SITE_MANAGER assigned) → `record_transaction RECEIVE` |
| GET | `/api/v1/inventory/transfers/` | auth + X-Company-ID | List |
| POST | `/api/v1/inventory/transfers/` | auth + X-Company-ID | `source/destination` + `items` (material, quantity_requested) |
| GET/PATCH | `/api/v1/inventory/transfers/<uuid>/` | auth + X-Company-ID | `transfer_or_404` + operator check |
| POST | `/api/v1/inventory/transfers/<uuid>/dispatch/` | auth + X-Company-ID | `Idempotency-Key`, `DRAFT→DISPATCHED`, `record_transaction TRANSFER_OUT` per item |
| POST | `/api/v1/inventory/transfers/<uuid>/receive/` | auth + X-Company-ID | `items: [{id, quantity}]`, `DISPATCHED|PARTIALLY→RECEIVED`, `TRANSFER_IN` |
| POST | `/api/v1/inventory/transfers/<uuid>/cancel/` | auth + X-Company-ID | `DRAFT→CANCELLED` |
| POST | `/api/v1/inventory/usage/` | auth + X-Company-ID | `project, location (must be PROJECT_SITE of that project), material, quantity` → `USE` |
| POST | `/api/v1/inventory/adjustment/` | auth + X-Company-ID | **OWNER only**, `direction IN/OUT` → `ADJUSTMENT_IN/OUT` |
| POST | `/api/v1/inventory/transactions/<uuid>/reverse/` | auth + X-Company-ID | **OWNER only**, `MaterialTransaction.objects.filter(reversal_of=original).exists()` check (fixed from `hasattr`) |

All inventory mutating endpoints support `Idempotency-Key: <uuid>` where noted.

---

## 8. Workforce — `/api/v1/workers/` + `/api/v1/projects/<uuid>/workers/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/workers/` | auth + X-Company-ID | List |
| POST | `/api/v1/workers/` | auth + X-Company-ID | OWNER/PROJECT_MANAGER |
| GET/PATCH | `/api/v1/workers/<uuid>/` | auth + X-Company-ID | OWNER/PM |
| POST | `/api/v1/projects/<uuid>/workers/` | auth + X-Company-ID | Assign worker (checks `status==ACTIVE`, same company) |
| GET | `/api/v1/projects/<uuid>/workers/` | auth + X-Company-ID | List project workers |

---

## 9. Reports — `/api/v1/projects/<uuid>/reports/` + `/api/v1/reports/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/projects/<uuid>/reports/` | auth + X-Company-ID | List |
| POST | `/api/v1/projects/<uuid>/reports/` | auth + X-Company-ID | `can_manage_project`, validates `report_date` required ISO `YYYY-MM-DD`, `report_date` unique per project → 201 `Report` + `Revision v1 DRAFT` |
| GET | `/api/v1/reports/<uuid>/` | auth + X-Company-ID | Retrieve |
| POST | `/api/v1/reports/<uuid>/revisions/` | auth + X-Company-ID | `can_manage_project`, requires `revision_reason`, copies source (`approved_revision` or latest) → fails if no source |
| GET | `/api/v1/revisions/<uuid>/` | auth + X-Company-ID | Retrieve |
| PATCH | `/api/v1/revisions/<uuid>/` | auth + X-Company-ID | `editable` (DRAFT + `can_manage_project`), validates negative `progress_delta` requires OWNER/PM + reason |
| POST | `/api/v1/revisions/<uuid>/submit/` | auth + X-Company-ID | `DRAFT→SUBMITTED` |
| POST | `/api/v1/revisions/<uuid>/approve/` | auth + X-Company-ID | **OWNER/PROJECT_MANAGER** + `can_manage_project`, validates `0≤new_progress≤100`, handles superseded material usages via `ADJUSTMENT_IN` reversal then new `USE` |
| POST | `/api/v1/revisions/<uuid>/reject/` | auth + X-Company-ID | OWNER/PM |
| POST | `/api/v1/revisions/<uuid>/material-usages/` | auth + X-Company-ID | `editable`, validates material+location belong to company + project site |
| PATCH/DELETE | `/api/v1/material-usages/<uuid>/` | auth + X-Company-ID | `editable` |

---

## 10. Dashboard & Audit

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/dashboard/company/` | auth + X-Company-ID | `low_stock` (bool), `recent_stock_movements` (6), financial summary |
| GET | `/api/v1/dashboard/projects/<uuid>/` | auth + X-Company-ID | `financial_summary` + `category_rows` + `project_usage` |
| GET | `/api/v1/audit-logs/?page=1` | auth + X-Company-ID | **Paginated** 25, **OWNER only**, immutable |

AuditLog records `company, actor, actor_snapshot, action, entity_type, entity_id, before_state, after_state, request_id, ip_address, user_agent`.

---

## 11. Frontend integration notes

1. Base: `const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"`; `fetch(`${API_URL}${path}`, { headers: { Authorization: `Bearer ${token}`, "X-Company-ID": companyId }, credentials: "include" })`; auto-refresh on 401 via `fetch(`${API_URL}/auth/refresh/`)`.
2. Company switcher: `localStorage.buildtrack_company` + `<select>` in `components/shell.tsx`.
3. Postman: import `postman/BuildTrack.postman_collection.json`, set `baseUrl`, `accessToken`, `companyId` variables.
4. Media: `multipart/form-data` for attachments; backend `FileField` stores in `MEDIA_ROOT` `backend/media/` (DEBUG serves via `static()`).
5. Types: `frontend/src/utils/apiTypes.js` is legacy — prefer `frontend/lib/api.ts` generics.

---

## 12. Future (out of v1.1 scope)

- Pagination for `projects/materials/locations/transfers/reports` (currently bare arrays)
- Search via `Q` objects + `distinct` for projects/materials (currently `|` queryset union)
- Full `ArrayField` removal from `audit/models.py` (unused import)
- Redis `CACHES` wiring (compose has redis but no Django `CACHES`)
- Replace `FileField` with S3, add virus scan
- Approval hierarchy unification (budgets OWNER-only vs expenses OWNER/ACCOUNTANT vs reports OWNER/PM)

---

## Appendix A — Method matrix (live)

```
POST   /api/v1/auth/register/                      AllowAny
POST   /api/v1/auth/login/                         AllowAny
POST   /api/v1/auth/refresh/                       cookie
POST   /api/v1/auth/logout/                        auth
GET    /api/v1/auth/me/                            auth
POST   /api/v1/auth/password/reset/                AllowAny
POST   /api/v1/auth/password/reset/confirm/        AllowAny

GET    /api/v1/companies/                          auth
POST   /api/v1/companies/                          auth
GET    /api/v1/companies/<uuid>/                   auth + X-Company-ID
POST   /api/v1/companies/<uuid>/invitations/       auth + X-Company-ID (OWNER)
POST   /api/v1/companies/invitations/accept/       auth

GET    /api/v1/projects/                           auth + X-Company-ID
POST   /api/v1/projects/                           auth + X-Company-ID (OWNER/PM)
GET    /api/v1/projects/<uuid>/                    auth + X-Company-ID
PATCH  /api/v1/projects/<uuid>/                    auth + X-Company-ID (can_manage)
POST   /api/v1/projects/<uuid>/archive/            auth + X-Company-ID
GET    /api/v1/projects/<uuid>/assignments/        auth + X-Company-ID
POST   /api/v1/projects/<uuid>/assignments/        auth + X-Company-ID

GET    /api/v1/projects/<uuid>/budget/             auth + X-Company-ID
POST   /api/v1/projects/<uuid>/budget/             auth + X-Company-ID
POST   /api/v1/projects/<uuid>/budget/revisions/   auth + X-Company-ID
GET    /api/v1/budget-versions/<uuid>/             auth + X-Company-ID
PATCH  /api/v1/budget-versions/<uuid>/             auth + X-Company-ID (DRAFT)
POST   /api/v1/budget-versions/<uuid>/submit/      auth + X-Company-ID
POST   /api/v1/budget-versions/<uuid>/approve/     auth + X-Company-ID (OWNER)
POST   /api/v1/budget-versions/<uuid>/reject/      auth + X-Company-ID (OWNER)

GET    /api/v1/suppliers/                          auth + X-Company-ID
POST   /api/v1/suppliers/                          auth + X-Company-ID (OWNER/ACC)
GET    /api/v1/expenses/                           auth + X-Company-ID (paginated)
POST   /api/v1/expenses/                           auth + X-Company-ID (Idempotency-Key)
POST   /api/v1/expenses/<uuid>/submit|approve|reject|reverse   auth + X-Company-ID
POST   /api/v1/expenses/<uuid>/attachments/        auth + X-Company-ID

GET    /api/v1/materials/                          auth + X-Company-ID
POST   /api/v1/materials/                          auth + X-Company-ID (OWNER)
GET    /api/v1/inventory/locations/                auth + X-Company-ID
GET    /api/v1/inventory/balances/                 auth + X-Company-ID
GET    /api/v1/inventory/transactions/             auth + X-Company-ID (paginated)
POST   /api/v1/inventory/receipt|transfers|usage|adjustment   auth + X-Company-ID

GET    /api/v1/workers/                            auth + X-Company-ID
POST   /api/v1/workers/                            auth + X-Company-ID (OWNER/PM)

GET    /api/v1/projects/<uuid>/reports/            auth + X-Company-ID
POST   /api/v1/projects/<uuid>/reports/            auth + X-Company-ID
POST   /api/v1/reports/<uuid>/revisions/           auth + X-Company-ID
POST   /api/v1/revisions/<uuid>/submit|approve|reject  auth + X-Company-ID

GET    /api/v1/dashboard/company/                  auth + X-Company-ID
GET    /api/v1/dashboard/projects/<uuid>/         auth + X-Company-ID
GET    /api/v1/audit-logs/                         auth + X-Company-ID (OWNER, paginated)
```
