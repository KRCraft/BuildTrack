# BuildTrack Frontend

Next.js 15 App Router (primary, port 3000) + legacy Vite SPA (fallback, port 5173) + Tailwind CSS.

## Setup

```bash
cd frontend
npm install
npm run dev        # Next.js -> http://localhost:3000
# legacy Vite (optional):
npx vite --port 5173
```

Env: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` (see `.env.example`). Legacy Vite reads `VITE_API_URL` fallback or `API_BASE_URL` env-aware.

## Structure

- `app/` — Next.js App Router (dashboard, projects/[id], inventory, expenses, materials, suppliers, team, settings, login, register)
- `components/` — `shell.tsx`, `auth-provider.tsx` (Bearer + X-Company-ID), `ui.tsx`, `expenses-page.tsx`
- `lib/api.ts` — fetch wrapper (`Bearer` + `X-Company-ID` + `credentials:include` + auto-refresh on 401)
- `src/` — legacy Vite SPA (kept, fixed)
  - `src/App.jsx` → imports `legacy-vite-pages/` (Home, Services, Projects, ProjectDetail, About, Contact, GetQuote, Dashboard)
  - `src/api/client.js` — axios (Bearer + X-Company-ID, env-aware baseURL /api/v1)
  - `src/components/`, `src/hooks/useProjects.js`, `src/context/AuthContext.jsx`, `src/utils/constants.js`
- `vite.config.js` — Vite 5173 proxy `/api` → `http://localhost:8000`
- `tailwind.config.ts` — content covers `app, components, lib, src`

## Routes (Next.js)

| Path | Page |
|------|------|
| `/` | redirect → `/dashboard` (`app/page.tsx`) |
| `/dashboard` | Company dashboard (`app/dashboard/page.tsx`) |
| `/projects` | List (`app/projects/page.tsx`, paginated 25) |
| `/projects/new` | Create |
| `/projects/[id]` | Detail + assignments, budget, expenses, materials |
| `/inventory` | Inventory balances |
| `/inventory/transfers` | Transfers list |
| `/materials` | Materials |
| `/expenses` | Expenses (paginated) |
| `/suppliers`, `/team`, `/settings` | CRUD |

Legacy Vite routes (`src/App.jsx`): `/`, `/services`, `/projects`, `/projects/:id`, `/about`, `/contact`, `/get-quote`, `/dashboard` (stub AuthContext `localStorage.buildtrack_token` → now `Bearer`).

## Backend contract

Expects Django at `http://localhost:8000/api/v1` (`X-Company-ID` required):

- `POST /api/v1/auth/register|login|refresh|me` — `{email, first_name, last_name, password}`
- `GET /api/v1/companies/` + `X-Company-ID`
- `GET /api/v1/projects/?search=&status=&page=1` (Q search, paginated), `POST /api/v1/projects/` (OWNER/PM)
- `GET /api/v1/projects/<uuid>/budget/` → 404 if none, budgets/expenses/inventory/workforce/reports under `/api/v1/`
- See `docs/API_CONTRACT.md v1.1` and Postman `postman/BuildTrack.postman_collection.json` (variables `baseUrl`, `accessToken`, `companyId`).
