@echo off
REM BuildTrack - run backend + frontend in dev mode (Windows)
REM Usage: scripts\run_dev.bat

echo Starting BuildTrack dev servers...

REM Backend (Django :8000)
start "BuildTrack Backend" cmd /k "cd /d %~dp0..\backend && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python manage.py runserver 8000"

REM Frontend (Next.js :3000)
start "BuildTrack Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev -- --port 3000"

echo Backend:  http://localhost:8000/api/v1/
echo Frontend: http://localhost:3000/
