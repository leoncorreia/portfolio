# Single Vite dev server on 127.0.0.1:5173 (proxies /api and /health → backend :8000).
# Stops whatever is listening on 5173–5176 so old duplicate Vite processes don’t linger.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

foreach ($port in 5173, 5174, 5175, 5176) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

npm run dev
