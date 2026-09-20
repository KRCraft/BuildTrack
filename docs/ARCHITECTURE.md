# BuildTrack Architecture

## Monorepo Overview

```text
                +------------------+
                |  Next.js 15      |
                |  localhost:3000  |  (Vite legacy :5173)
                |  app/components/ |
                |  lib/api.ts      |
                +--------+---------+
                         | HTTP / JSON
                         | CORS allowed (3000 + 5173)
                         v
                +--------+---------+
                |  Django DRF      |
                |  localhost:8000  |
                |  /api/v1/* + /admin |
                +--------+---------+
                     |         |
            +--------+---+ +---+--------+
            | PostgreSQL | | Redis      |
            | :5432      | | :6379 opt  |
            | primary DB | | cache/Celery|
            +------------+ +------------+
```

- `backend/` — Django REST Framework API, JWT HttpOnly refresh, 11 active apps + legacy.
- `frontend/` — Next.js 15 App Router (primary :3000) + legacy Vite SPA (:5173 fallback).
- `docker-compose.yml` — orchestrates db (healthcheck), redis, backend (gunicorn+healthcheck), frontend (depends_on healthy).
- `postman/` — API collection (legacy `/api/` — regenerate to `/api/v1/` + X-Company-ID).
- `scripts/` — local dev automation (Next.js :3000).

## Backend Layout

```text
backend/
├── config/
│   ├── settings.py   # DRF, SimpleJWT, corsheaders, throttling, DB via POSTGRES_* or DATABASE_URL, CORS 3000+5173
│   ├── urls.py       # /admin/, /api/v1/auth|companies|projects|budgets|expenses|inventory|workforce|reports|dashboard|audit-logs
│   ├── wsgi.py / asgi.py
├── apps/
│   ├── accounts/      # Auth (email, HttpOnly refresh cookie at /api/v1/auth/)
│   ├── companies/     # Company, Membership, Invitations
│   ├── projects/      # Project (DRAFT/ACTIVE/ON_HOLD/COMPLETED/ARCHIVED) + assignments
│   ├── budgets/       # Budget + BudgetVersion + BudgetCategory
│   ├── expenses/      # Expense, Supplier, approvals, attachments
│   ├── inventory/     # Material, InventoryLocation, Balance, Transactions, Transfers
│   ├── workforce/     # Workers
│   ├── reports/       # DailyReport + Revisions
│   ├── audit/         # Immutable AuditLog
│   ├── dashboard/     # dashboards
│   ├── common/        # UUIDTimeStampedModel, tenant helpers
│   └── clients|quotes|contact # LEGACY (not in INSTALLED_APPS)
├── requirements.txt  # django, drf, simplejwt, cors, psycopg2-binary, gunicorn, whitenoise, environ, pillow
└── manage.py
```

API prefix convention: `/api/v1/<resource>/` (e.g. `/api/v1/projects/`, `/api/v1/budgets/`).
Auth endpoints: `/api/v1/auth/register|login|refresh|logout|me`, `/api/v1/companies/`, `/api/v1/projects/`.

## Frontend Layout

```text
frontend/
├── app/               # Next.js App Router (dashboard, projects, inventory, expenses, etc.)
├── components/        # shell, auth-provider, ui.tsx
├── lib/api.ts         # fetch wrapper, NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1, Bearer + X-Company-ID, credentials:include, auto-refresh
├── src/
│   ├── api/client.js      # axios instance, baseURL=NEXT_PUBLIC_API_URL fallback, Bearer + X-Company-ID
│   ├── context/AuthContext.jsx
│   ├── legacy-vite-pages/ # Dashboard, Projects, Quotes, Clients, etc.
│   ├── components/        # Navbar, Cards, Forms
│   ├── hooks/ utils/ data/ assets/ styles/
```

Legacy Vite path (`src/`, `vite.config.js` :5173) kept for fallback; primary is Next.js.

## CORS

- Backend uses `django-cors-headers`.
- Dev: `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000`.
- `CORS_ALLOW_CREDENTIALS=True` required for HttpOnly refresh cookie (`credentials:include`).
- Middleware order matters: `CorsMiddleware` must be above `CommonMiddleware`.
- Prod: set explicit Vercel URL, never `CORS_ALLOW_ALL_ORIGINS=True`.

```python
# config/settings.py (excerpt)
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True
```

Frontend sends `Authorization: Bearer <access>` + `X-Company-ID` via `lib/api.ts`; refresh token in HttpOnly cookie at `/api/v1/auth/refresh/` (SameSite=Lax, Secure in prod).

## Auth Flow (JWT — SimpleJWT, HttpOnly refresh)

```text
1. POST /api/v1/auth/register/  {email, first_name, last_name, password} -> 201
2. POST /api/v1/auth/login/      {email, password} -> {access, refresh} + Set-Cookie buildtrack_refresh (HttpOnly, Path=/api/v1/auth/)
3. Client stores access in sessionStorage, company in localStorage, sets fetch Authorization: Bearer <access> + X-Company-ID
4. GET /api/v1/projects/ with Authorization: Bearer <access> + X-Company-ID -> 200 (paginated)
5. On 401 (expired access 15min): POST /api/v1/auth/refresh/ (credentials:include, cookie) -> new access
6. Logout: POST /api/v1/auth/logout/ (blacklist refresh, delete cookie)
```

Frontend `auth-provider.tsx` holds `user + companies`, `shell.tsx` company switcher. Backend DRF default: `IsAuthenticated` for domain APIs, `AllowAny` for register/login.

## Deployment Options

### Option 1 — Render (backend) + Vercel (frontend) [recommended]

- Backend → Render Web Service:
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`
  - Env: `DJANGO_SECRET_KEY, DJANGO_DEBUG=False, DATABASE_URL (Render Postgres), CORS_ALLOWED_ORIGINS=https://<vercel-app>.vercel.app, DJANGO_ALLOWED_HOSTS`
  - Run `python manage.py migrate` on deploy (or via docker-compose command).
- Frontend → Vercel:
  - Root: `frontend/`, Build: `npm run build`, Output: `.next` (standalone)
  - Env: `NEXT_PUBLIC_API_URL=https://<render-backend>.onrender.com/api/v1`
- DB → Render Postgres (or Neon/Supabase). Redis → Upstash (optional).

### Option 2 — Full Docker (VPS)

- `docker-compose up -d --build` on any VPS (backend gunicorn, Next :3000).
- Put Caddy/Nginx in front for TLS. Backend serves DRF only; frontend via Next.

### Option 3 — All-in-one Docker

- Multi-stage frontend build → served by backend `staticfiles/` or Nginx container.

## Non-Goals (MVP)

No Celery workers, no S3 uploads, no payment gateway yet. Redis is provisioned in compose but optional until Phase 2 background jobs (email, reminders). Throttling is enabled (anon 100/hour, user 1000/hour).
