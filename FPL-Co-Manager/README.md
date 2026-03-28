# FPL AI Co-Manager

Hackathon-ready **Fantasy Premier League** assistant: deterministic lineup and transfers, **Kimi** explanations via **GMI**, **HydraDB** session memory, **Dify** workflow ping after each analyze, **React** UI.

## Architecture

- **Backend:** Python 3.11, FastAPI, Pydantic, SQLAlchemy (SQLite), HTTPX for FPL public API.
- **Frontend:** React 18, Vite, TypeScript; `fetch` calls proxied to the API in dev.
- **Photon Spectrum** ([photon.codes/spectrum](https://photon.codes/spectrum)): messaging-channel framework (Telegram, WhatsApp, iMessage, etc.) for agents — **not** the browser UI here; optional future integration (see [INTEGRATION_SETUP.md](docs/INTEGRATION_SETUP.md)).
- **Layers:** `routes/` → `services/` → `repositories/` & `providers/`; `schemas.py` for API contracts.

```
FPL-Co-Manager/
  backend/     # FastAPI app
  frontend/    # Vite React UI
```

## Integration (keys + consoles)

Setup and behavior vs acceptance criteria: **[docs/INTEGRATION_SETUP.md](docs/INTEGRATION_SETUP.md)** and **[docs/ACCEPTANCE_AUDIT.md](docs/ACCEPTANCE_AUDIT.md)**. Copy `backend/.env.example` → `backend/.env` (never commit `.env`).

### Dify workflow

1. Put your **Workflow API key** in **`backend/.env`** as **`DIFY_API_KEY`** (from Dify: published Workflow app → **API Access**).
2. Set **`DIFY_BASE_URL`** to your API root with `/v1` (e.g. `https://api.dify.ai/v1`).
3. In the Dify **START** node, create input variables whose **names** match **`DIFY_INPUT_*`** in `.env` (defaults: `squad`, `recommendation`, `deterministic_explanation`, `user_id`). Use **Paragraph** for long JSON/text. In the **LLM** node, **do not type `{{...}}` by hand** — press **`/`** and pick each variable from the menu so Dify wires START inputs (see [Dify lesson 3](https://docs.dify.ai/en/use-dify/tutorials/workflow-101/lesson-03)). Putting squad / recommendation / reasoning in a **User** message with `/` inserts is more reliable than only the system box. The optional **Context** slot is for RAG, not START inputs.
4. **Optional:** Set **`DIFY_INPUT_BUNDLE=fpl_context`** (any unused name) in `backend/.env`, add a matching **Paragraph** variable on START (e.g. `fpl_context`), and use **only** that one variable in the prompt via **`/`**. The backend still sends the four original keys for compatibility, plus the bundle.
5. Each successful **`POST /api/analyze`** calls **`POST {DIFY_BASE_URL}/workflows/run`** and appends any returned text under `--- Dify workflow note ---` in the recommendation explanation (after deterministic + Kimi). Response flags: **`dify_used`**, **`dify_error`**.

## Quick start

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\run-dev.ps1
```

Or see **`backend/README.md`** for activate vs direct `\.venv\Scripts\python.exe` usage.

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for OpenAPI.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **[http://127.0.0.1:5173](http://127.0.0.1:5173)** (Vite binds that host/port with `strictPort` so it stays on 5173). On Windows you can run **`frontend/run-dev.ps1`** first to free duplicate listeners on 5173–5176, then start dev. The dev server proxies `/api` and `/health` to port 8000 by default; if the API uses another port, set `VITE_DEV_PROXY_TARGET` in `frontend/.env` (see `frontend/.env.example`).

## Demo flow

1. Start backend and frontend.
2. Enter a **public FPL entry ID** (from the official site) or click **Demo team ID** to prefill a sample.
3. Click **Import team** (requires network access to `fantasy.premierleague.com`).
4. Click **Analyze team** to get starting XI, bench, captain, vice, transfers or roll, and explanation.
5. Run again with **Use prior session memory** to see the previous summary line.

If import fails (network, invalid ID), use **Manual squad** and paste a JSON `Squad` matching the API schema.

## API routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness |
| POST | `/api/import-team` | Import squad from FPL public endpoints |
| POST | `/api/analyze` | Optimize + Kimi (GMI) explanation + SQLite/Hydra + Dify workflow |
| GET | `/api/memory/{user_id}` | Latest stored recommendation |
| GET | `/api/memory/{user_id}/sessions` | Recent sessions (limit query) |
| POST | `/api/compare-last` | Compare last stored run vs fresh analysis |
| POST | `/api/parse-image` | Kimi vision via GMI + JSON parse |
| GET | `/api/demo-hints` | Sample team ID hint |

## Assumptions

- **Squad source:** The public API returns picks per gameweek. The app uses the current event when available, otherwise falls back to recent gameweeks (see comments in `providers/fpl_public_api.py`).
- **Scoring:** Heuristic blend of form, fixture proxy (team strength), minutes, ICT, injury flags — not official FPL projections.
- **Transfers:** Full player pool from bootstrap minus your squad; budget and 3-players-per-club rules enforced; gains are heuristic.

## How to extend later

- **Kimi explanations:** `providers/kimi_provider.py` (`KimiViaGMIProvider`) — `GMI_API_KEY`, `GMI_BASE_URL`, `KIMI_MODEL`.
- **Kimi vision / image import:** `providers/image_parser_provider.py` — same GMI + `KIMI_VISION_MODEL`.
- **Dify orchestration:** `providers/dify_workflow.py` — `POST /workflows/run` after each analyze; extend the workflow in Dify’s console.
- **HydraDB:** `providers/hydra_memory.py` — structured write + recall-based read for latest session.
- **Other UIs:** Same REST contract as `frontend/README.md`; this repo ships **React + Vite** only. [Photon Spectrum](https://photon.codes/spectrum) would be a separate surface (chat channels), not a drop-in replacement for this web app.

## Hackathon scope

- End-to-end **import → analyze → persist → show memory** in one repo.
- **No secrets** in code; `.env.example` lists placeholders.
- **Deterministic core** so judges see repeatable logic; stubs document where AI upgrades plug in.

## Known limitations

- Public FPL API has no authenticated “transfer market” for a specific user; transfer suggestions use bootstrap prices and heuristics.
- Image parsing depends on GMI + `KIMI_VISION_MODEL`; model output quality varies.
- Captain/lineup logic does not model chips, autosub order in full detail, or real-time injury news feeds.

## License

Project scaffold for hackathon / demo use — adjust as needed.
