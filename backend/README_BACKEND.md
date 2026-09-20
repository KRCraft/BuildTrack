# BuildTrack Backend (Django + DRF)

## Quickstart

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/`

## Endpoints

- `GET /api/projects/` — list (?status=ongoing|completed|upcoming, ?search=, ?ordering=)
- `GET /api/projects/<slug>/` — detail
- `POST /api/auth/token/` + `POST /api/auth/token/refresh/` — JWT
- `GET/POST /api/clients/` (auth required for write)
- `POST /api/quotes/` — public quote request; `GET /api/quotes/` requires auth
- `POST /api/contact/messages/` — public contact; list requires auth
- `GET /api/contact/testimonials/` — public approved list

## Env vars

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_ALL`
- Prod DB: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
  (uncomment Postgres `DATABASES` block in `config/settings.py`)

## Media

`MEDIA_URL=/media/`, `MEDIA_ROOT=backend/media/`. Served by Django only when `DEBUG=True`.
In prod, use S3 / WhiteNoise / Nginx for `staticfiles/` + `media/`.
