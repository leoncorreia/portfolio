# SceneProof

SceneProof turns policy documents and SOPs into structured training videos: extraction, scene planning, storyboards, narration, optional presenter avatars, validation against source text, and an assembly-ready media manifest.

Built for the **Beta University Seed Agents Challenge**. Media and reasoning are wired through **Seed 2.0**, **Seedream 5.0**, **Seedance 2.0**, **Seed Speech**, and **OmniHuman** with **mock-safe providers** so the product runs end-to-end locally without API keys.

## Architecture

- `frontend/` — React + Vite + TypeScript SPA (upload, review, output dashboards).
- `backend/` — FastAPI + Pydantic + async job orchestration + local JSON/file storage under `DATA_DIR`.
- Providers under `backend/app/providers/` encapsulate each vendor; missing credentials automatically fall back to deterministic demo payloads (no crashes).

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env   # optional: fill keys later; also works if .env lives at repo root
python -m uvicorn app.main:app --reload --port 8000
```

Settings load **both** `SceneProof/.env` and `backend/.env` (backend wins on duplicate keys), so you can keep secrets at repo root or next to the API.

If `uvicorn` is not found, always use `python -m uvicorn` as shown above.

Health check: `http://127.0.0.1:8000/api/health`

### One-shot dev (Windows)

From the repo root:

```powershell
.\scripts\dev.ps1
```

This opens a second terminal for the API and runs the Vite dev server in the current window.

Uploaded assets and job JSON are written to `backend/data/` (override with `DATA_DIR`).

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` and `/media` to the backend.

### Hackathon deploy on Render (recommended for your credits)

This repo already includes a Render Blueprint at `SceneProof/render.yaml` that creates:

- `sceneproof-api` (FastAPI, **Starter** plan, persistent disk)
- `sceneproof-web` (static frontend)

#### One-time deploy steps

1. In Render dashboard: **New → Blueprint**
2. Connect repo: [`https://github.com/leoncorreia/portfolio`](https://github.com/leoncorreia/portfolio)
3. Set **Blueprint path** to: `SceneProof/render.yaml`
4. Click **Apply**

Render will provision both services and assign `*.onrender.com` URLs.

#### Wire environment values after first deploy

After URLs exist, set these service env vars in Render:

- On **sceneproof-web**:
  - `VITE_API_BASE_URL=https://<sceneproof-api>.onrender.com`
- On **sceneproof-api**:
  - `CORS_ORIGINS=https://<sceneproof-web>.onrender.com,http://localhost:5173`

Then redeploy both services once.

#### Why this setup

- `sceneproof-api` runs on **Starter**, so no free-tier sleep/cold starts during demos.
- API data persists to Render disk (`/var/data`) because `DATA_DIR=/var/data` is configured.
- `DEMO_MODE=true` is set by default in the blueprint, so the app works end-to-end even without real provider keys.

#### Optional live provider keys

To use real Seed/OmniHuman APIs, add keys/base URLs from `.env.example` to **sceneproof-api** env vars and set `DEMO_MODE=false`.

#### What to submit

Submit the **sceneproof-web Render URL** to judges (plus repo URL if requested).

### Production-ish frontend build

```powershell
cd frontend
npm run build
npm run preview
```

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness + provider configuration flags |
| `POST` | `/api/jobs` | Multipart job creation (`raw_text`, optional `document`, optional `presenter_image`, `audience`, `language`, `style_preset`) |
| `GET` | `/api/jobs/{job_id}` | Job status, progress, partial outputs |
| `POST` | `/api/jobs/{job_id}/review` | Runs ingestion → Seed 2.0 extraction → Seed 2.0 planning |
| `POST` | `/api/jobs/{job_id}/generate` | Runs Seedream, Seed Speech, Seedance, optional OmniHuman, validation, assembly |
| `GET` | `/api/jobs/{job_id}/result` | Final `GenerationResult` (409 until `completed`) |
| `POST` | `/api/jobs/{job_id}/regenerate-scene/{scene_id}` | Placeholder hook for per-scene refresh |

## GitHub repository

Initialize and publish (requires [GitHub CLI](https://cli.github.com/)):

```powershell
cd SceneProof
git init
git add .
git commit -m "Initial SceneProof full-stack implementation"
gh repo create SceneProof --private --source . --remote origin --push
```

Without `gh`, create an empty repository in the GitHub UI, then:

```powershell
git remote add origin https://github.com/<you>/SceneProof.git
git push -u origin main
```

## Notes for judges / investors

- **Demo mode** is the default whenever keys and base URLs are absent; providers still return normalized structures your UI can render.
- **Assembly** currently emits a JSON program manifest plus typed `MediaAsset` metadata; binary muxing can plug into the same `AssemblyService` interface without changing API contracts.
- **Security**: never commit `.env`; use `.env.example` as the single source of variable names.

## License

Hackathon / demonstration use unless otherwise specified.
