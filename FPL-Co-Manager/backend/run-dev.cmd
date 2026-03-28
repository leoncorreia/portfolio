@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set "API_PORT=8000") else set "API_PORT=%~1"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Run: python -m venv .venv ^&^& .venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)
if not "%API_PORT%"=="8000" echo API port %API_PORT% — set VITE_DEV_PROXY_TARGET=http://127.0.0.1:%API_PORT% in frontend/.env
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port %API_PORT%
