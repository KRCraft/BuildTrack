@echo off
REM BuildTrack - first-time setup (Windows)
REM Usage: scripts\setup.bat

echo [1/4] Checking Python...
python --version || (echo Python not found. Install Python 3.12+. && exit /b 1)

echo [2/4] Setting up backend...
cd /d %~dp0..\backend
if not exist venv (python -m venv venv)
call venv\Scripts\activate.bat
pip install -r requirements.txt
if not exist .env (copy .env.example .env 2>nul || echo No .env.example, skipping.)
python manage.py migrate
echo Backend setup done.

echo [3/4] Setting up frontend...
cd /d %~dp0..\frontend
where npm >nul 2>nul || (echo Node.js/npm not found. Install Node 20+. && exit /b 1)
call npm install
if not exist .env (echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1> .env)
echo Frontend setup done.

echo [4/4] Done. Run scripts\run_dev.bat to start dev servers.
