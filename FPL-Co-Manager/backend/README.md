# FPL AI Co-Manager — Backend

FastAPI: FPL import, **deterministic** lineup/transfer optimization, **Kimi-via-GMI** explanations, SQLite + optional **HydraDB** structured memory.

## Setup (Windows)

**Use the project virtualenv** so `uvicorn` and dependencies resolve correctly.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Run the API (either):

```powershell
.\run-dev.ps1
```

Alternate API port (e.g. if 8000 is in use or blocked): `.\run-dev.ps1 -Port 8001` or `run-dev.cmd 8001`, then set `VITE_DEV_PROXY_TARGET=http://127.0.0.1:8001` in `frontend/.env`.

or, after `Activate.ps1`:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or without activating: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

**If `Activate.ps1` is blocked:** `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use `run-dev.cmd` / `run-dev.ps1` (calls `python.exe` inside `.venv` directly).

## Architecture (roles)

| Path | Role |
|------|------|
| `services/optimizer_service.py`, `transfer_service.py`, … | Deterministic decisions |
| `providers/gmi_inference.py` | GMI HTTP transport only (`/chat/completions`) |
| `providers/kimi_provider.py` | Kimi explanation + vision **via GMI** (`KIMI_MODEL` / `KIMI_VISION_MODEL`) |
| `providers/explanation_provider.py` | Interface for narrative layer only |
| `providers/dify_workflow.py` | `POST /workflows/run` after each analyze; append note to explanation |
| `providers/hydra_memory.py` | HydraDB structured session persistence |
| `repositories/` | SQLite recommendation history |

See **`../docs/INTEGRATION_SETUP.md`** for env vars and consoles.

## Environment

`.env.example` lists `GMI_*`, `KIMI_MODEL`, `HYDRADB_*`, optional `DIFY_*`.

## Smoke test

```bash
curl http://127.0.0.1:8000/health
```
