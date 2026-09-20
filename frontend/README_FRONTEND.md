# BuildTrack Frontend

React 18 + Vite + React Router + Tailwind CSS + Axios.

## Setup

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173` and proxies `/api` to `http://localhost:8000`.

## Structure

- `src/App.jsx` — routes
- `src/api/client.js` — axios instance (`baseURL: http://localhost:8000/api`)
- `src/components/` — Navbar, Footer, Hero, ServicesGrid, ProjectCard, QuoteForm, Loader
- `src/pages/` — Home, Services, Projects, ProjectDetail, About, Contact, GetQuote, Dashboard
- `src/hooks/useProjects.js` — fetch project list
- `src/context/AuthContext.jsx` — auth stub (localStorage token)
- `src/utils/constants.js` — nav links, services, constants

## Routes

| Path | Page |
|------|------|
| `/` | Home |
| `/services` | Services |
| `/projects` | Projects |
| `/projects/:id` | ProjectDetail |
| `/about` | About |
| `/contact` | Contact |
| `/get-quote` | GetQuote |
| `/dashboard` | Dashboard (client project list stub) |

## Backend contract

Expects Django/DRF at `http://localhost:8000/api`:
- `GET /projects/` / `GET /projects/:id/`
- `POST /quotes/` — `{ name, email, phone, service_type, message, budget }`
- `POST /contact/` — `{ name, email, message }`
