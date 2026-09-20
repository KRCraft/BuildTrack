# BuildTrack Roadmap

## MVP (v0.1 — current sprint)

Goal: usable internal tool — quotes, projects, clients, contact.

- [ ] Auth: register / login / refresh / logout (JWT), ProtectedRoute, AuthContext
- [ ] Dashboard: counts (projects, quotes, clients), recent items
- [ ] Clients CRUD: name, email, phone, company, search
- [ ] Projects CRUD: title, client FK, status (`inquiry → quoted → in_progress → completed`), budget, dates
- [ ] Quotes CRUD: client/project FK, line items, total, status (`draft → sent → accepted → rejected`)
- [ ] Contact form: public submit → stored → admin list
- [ ] Admin: Django admin registered for all models
- [ ] API docs: Postman collection + seed data
- [ ] DevOps: Dockerfiles, compose, setup/run scripts, docs (this agent)

Exit criteria: `docker-compose up` gives working frontend + backend; all MVP endpoints tested via Postman.

## Phase 2 (v0.2 — payments + project tracking depth)

- Auth hardening: HttpOnly refresh cookies, token rotation + blacklist, roles (admin/staff/client)
- Dashboard v2: charts (revenue, project status), overdue alerts
- Payments / milestones: `Payment` model (project FK, amount, due_date, paid flag), payment history, outstanding balance
- Project tracking: tasks/checklist per project, progress %, file attachments (S3/media), activity timeline
- Quotes v2: PDF export, email send, quote → project conversion
- Notifications: email on quote sent / payment due (Celery + Redis)
- Client portal (read-only): client login sees own projects/quotes/payments

## Phase 3 (v1.0 — production hardening)

- Reporting: revenue reports, CSV export
- Permissions: object-level (users see only assigned projects)
- Search/filter/pagination polish on all lists
- E2E tests (Playwright) + CI (GitHub Actions: lint, test, build)
- Deployment: Render + Vercel live, custom domain, Sentry monitoring, backups
- Mobile-responsive audit + accessibility pass

## Out of Scope (for now)

Multi-tenant SaaS billing, native mobile apps, real-time chat, accounting integrations.
