#!/usr/bin/env bash
# BuildTrack - run backend + frontend in dev mode (macOS/Linux)
# Usage: ./scripts/run_dev.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting BuildTrack dev servers..."

# Backend
(
  cd "$ROOT/backend"
  if [ -d "venv" ]; then source venv/bin/activate; fi
  python manage.py runserver 8000 &
  echo $! > /tmp/buildtrack-backend.pid
) &

# Frontend (Next.js :3000 - also supports Vite legacy on 5173 if needed)
(
  cd "$ROOT/frontend"
  npm run dev -- --port 3000 &
  echo $! > /tmp/buildtrack-frontend.pid
) &

wait
