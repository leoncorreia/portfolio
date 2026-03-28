# Run API with the project venv (PowerShell). From backend/: .\run-dev.ps1 [-Port 8001]
param([int]$Port = 8000)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
$py = Join-Path $here ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing .venv. Run: python -m venv .venv && .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}
if ($Port -ne 8000) {
    Write-Host "API port $Port — set VITE_DEV_PROXY_TARGET=http://127.0.0.1:$Port in frontend/.env for the Vite proxy."
}
& $py -m uvicorn app.main:app --reload --host 127.0.0.1 --port $Port
