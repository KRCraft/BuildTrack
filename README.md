# BuildTrack

> Multi-tenant construction operations platform for projects, teams, and site delivery.

## Vision

Small construction firms still run on spreadsheets, WhatsApp, and paper quotes.
BuildTrack gives them a single dashboard to:

- Create and send professional **quotes** in minutes
- Track **projects** from inquiry → in-progress → completed
- Manage **clients** and contact history
- Plan **payments / milestones** (Phase 2)
- Give clients a transparent view of progress (Phase 2+)

The first usable vertical slice provides authentication, company workspaces, roles, project management, a dashboard, and immutable audit records.

## Tech Stack

| Layer    | Tech |
|----------|------|
| Backend  | Django 5 + Django REST Framework + SimpleJWT + PostgreSQL |
| Frontend | Next.js App Router + TypeScript + Tailwind CSS |
| DevOps   | Docker Compose (Django:8000, Next.js:3000, PostgreSQL:5432, Redis:6379) |
| Docs/API | Postman collection in `postman/` |

## Project Structure

```text
BuildTrack/
├── backend/               # Django REST API (port 8000)
│   ├── config/            # settings.py, urls.py, wsgi.py, asgi.py
│   ├── apps/              # 11 active apps: accounts, companies, projects, budgets, expenses, inventory, workforce, reports, audit, dashboard, common (+ legacy clients/quotes/contact)
│   │   ├── accounts/      # Auth (JWT, HttpOnly refresh)
│   │   ├── companies/     # Multi-tenant workspaces
│   │   ├── projects/      # Project tracking (DRAFT→ACTIVE→COMPLETED)
│   │   ├── budgets/       # Budget versions & categories
│   │   ├── expenses/      # Expenses & approvals
│   │   ├── inventory/     # Materials, balances, transfers
│   │   ├── workforce/     # Workers & assignments
│   │   ├── reports/       # Daily reports & revisions
│   │   └── ...            # audit, dashboard
│   ├── requirements.txt   # + gunicorn, whitenoise
│   ├── manage.py
│   └── Dockerfile         # gunicorn prod, non-root user
├── frontend/              # Next.js 15 App Router (port 3000) + legacy Vite SPA (port 5173 fallback)
│   ├── app/               # Next.js App Router (dashboard, projects, inventory, expenses, etc.)
│   ├── components/        # Next.js UI (shell, auth-provider)
│   ├── lib/               # api.ts (Bearer + X-Company-ID + auto-refresh)
│   ├── src/               # Legacy Vite SPA (legacy-vite-pages, api/client.js, context/AuthContext)
│   │   ├── legacy-vite-pages/ # migrated pages (Home, Projects, etc.)
│   │   ├── api/           # axios client (Bearer)
│   │   ├── components/    # reusable UI
│   │   ├── context/       # AuthContext
│   │   └── utils/ data/ hooks/ styles/
│   ├── package.json       # next dev / build / start
│   ├── vite.config.js     # legacy Vite 5173 proxy
│   └── Dockerfile         # Next.js dev :3000
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── postman/               # API collection (other agent)
├── scripts/
│   ├── setup.bat / setup.sh
│   └── run_dev.bat / run_dev.sh
├── docker-compose.yml
├── .gitignore
├── README.md
└── PROJECT_STRUCTURE.txt
```

Full tree: see `PROJECT_STRUCTURE.txt`.

## Quickstart

### Option A — Docker (recommended)

```bash
docker compose up --build
# backend:  http://localhost:8000/api/v1/
# frontend: http://localhost:3000/
# admin:    http://localhost:8000/admin/
```

### Option B — Local dev (Windows)

```bat
scripts\setup.bat
scripts\run_dev.bat
```

### Option C — Local dev (macOS / Linux)

```bash
chmod +x scripts/setup.sh scripts/run_dev.sh
./scripts/setup.sh
./scripts/run_dev.sh
```

### Manual quickstart

**Backend (Django):**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

API base: `http://localhost:8000/api/v1/`

**Frontend (Next.js 15):**

```bash
cd frontend
npm install
npm run dev   # -> http://localhost:3000
```

App: `http://localhost:3000/` (legacy Vite fallback: `vite --port 5173`)
Configure API URL in `frontend/.env`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Environment Variables

**backend/.env:**

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me-in-production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
POSTGRES_DB=buildtrack
POSTGRES_USER=buildtrack
POSTGRES_PASSWORD=buildtrack
POSTGRES_HOST=db
POSTGRES_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000
DATABASE_URL=postgres://buildtrack:buildtrack@db:5432/buildtrack  # optional override
```

**frontend/.env:**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Features & Roadmap

- [x] Monorepo scaffold (Django + React + Docker)
- [ ] MVP: JWT auth, dashboard, CRUD for clients/projects/quotes, contact form
- [ ] Phase 2: payments/milestones, file uploads, client portal, email notifications
- [ ] Phase 3: reporting, roles/permissions, deployment (Render + Vercel)

See `docs/ROADMAP.md` and `docs/ARCHITECTURE.md` for details.

## Team Workflow (5 agents)

- Agent 1: Backend core (config, apps)
- Agent 2: Frontend core (pages, components)
- Agent 3: Auth + API integration
- Agent 4: Testing + Postman + seed data
- Agent 5 (this): Root, DevOps, integration, docs — no backend/frontend core overwrites

## License

MIT (TBD).
