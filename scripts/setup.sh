#!/usr/bin/env bash
# BuildTrack - first-time setup (macOS/Linux)
# Usage: ./scripts/setup.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "[1/4] Checking Python..."
python3 --version

echo "[2/4] Setting up backend..."
cd "$ROOT/backend"
if [ ! -d "venv" ]; then python3 -m venv venv; fi
source venv/bin/activate
pip install -r requirements.txt
[ -f ".env.example" ] && [ ! -f ".env" ] && cp .env.example .env || true
python manage.py migrate
echo "Backend setup done."

echo "[3/4] Setting up frontend..."
cd "$ROOT/frontend"
npm install
[ ! -f ".env" ] && echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env || true
echo "Frontend setup done."

echo "[4/4] Done. Run ./scripts/run_dev.sh to start dev servers."
