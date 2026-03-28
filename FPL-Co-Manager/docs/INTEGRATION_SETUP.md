# Integration setup

This document matches **what the code does today**. See also [ACCEPTANCE_AUDIT.md](ACCEPTANCE_AUDIT.md).

## Roles

| Component | Responsibility |
|-----------|----------------|
| **React + Vite UI** | Browser client (this repo’s `frontend/`). |
| **FastAPI backend** | FPL import, deterministic optimizer, persistence, orchestration hooks. |
| **GMI Cloud** | HTTP inference: `GET /models`, `POST /chat/completions` (OpenAI-style JSON). |
| **Kimi** | Model **names** only (`KIMI_MODEL`, `KIMI_VISION_MODEL`) passed to GMI — not a second API key. |
| **Dify** | After each analyze: `POST /workflows/run` with squad + recommendation + deterministic text (orchestration). |
| **HydraDB** | Structured session JSON write + recall-based read for “latest” prior session per `user_id`. |
| **SQLite** | Local structured history; used if Hydra has no prior hit. |
| **Photon Spectrum** (optional) | [Spectrum](https://photon.codes/spectrum) connects agents to **messaging surfaces** (Telegram, WhatsApp, iMessage, Discord, etc.). It is **not** a React UI kit and is **not imported** in `frontend/` today. To “use Photon” in the hackathon sense, you would add a Spectrum-based worker or service that calls this backend’s REST API (or shares agent logic) — separate from the Vite app. See [github.com/photon-hq](https://github.com/photon-hq). |

There is **no** LLM provider fallback chain.

## Environment (`backend/.env`)

Copy `backend/.env.example` → `backend/.env`.

### GMI + Kimi

```env
GMI_API_KEY=...
GMI_BASE_URL=https://api.gmi-serving.com/v1
KIMI_MODEL=<exact id from GET .../models>
KIMI_VISION_MODEL=<exact id, often same as text model if multimodal>
```

On startup the app calls `GET {GMI_BASE_URL}/models` and **warns** if your model ids are missing from the list.

**Request format** (implemented in `providers/gmi_inference.py`):

```http
POST {GMI_BASE_URL}/chat/completions
Authorization: Bearer <GMI_API_KEY>
Content-Type: application/json

{"model":"<KIMI_MODEL>","messages":[...],"max_tokens":2048,"temperature":0.35}
```

Vision: same endpoint, `model`: `KIMI_VISION_MODEL`, user message with `image_url` + `text` parts.

### Dify

1. Publish a **Workflow** app. In the **START** node, add inputs whose **names** match `DIFY_INPUT_SQUAD`, `DIFY_INPUT_RECOMMENDATION`, `DIFY_INPUT_DETERMINISTIC`, `DIFY_INPUT_USER_ID` (defaults below). Use **Paragraph** for long JSON/text.
2. In the **LLM** node, insert those values with the **`/`** variable picker — typing `{{squad}}` manually usually leaves them **unwired**, so the model sees blanks and may ask the user to paste data. Prefer a **User** message line per field using `/`, per [Dify workflow lesson 3](https://docs.dify.ai/en/use-dify/tutorials/workflow-101/lesson-03).
3. **Optional:** Define `DIFY_INPUT_BUNDLE` (e.g. `fpl_context`), add that Paragraph on START, and reference only that variable via `/`. The backend fills it with a single markdown block (squad + recommendation + reasoning + user id) while still sending the four separate API keys.

4. **API Access** → copy the **Workflow** API key.

```env
DIFY_API_KEY=app-...
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_TIMEOUT_SECONDS=120
DIFY_INPUT_SQUAD=squad
DIFY_INPUT_RECOMMENDATION=recommendation
DIFY_INPUT_DETERMINISTIC=deterministic_explanation
DIFY_INPUT_USER_ID=user_id
# Optional: also send one combined markdown field (add same name on START + use / in LLM)
# DIFY_INPUT_BUNDLE=fpl_context
```

If `DIFY_API_KEY` is unset or `placeholder`, the workflow is not called (`dify_used=false` on `/api/analyze`).

The request body uses `"user": "<user_id>"` (same id as the analyze request) per Dify’s API.

### HydraDB

```env
HYDRADB_API_KEY=...
HYDRADB_TENANT_ID=...
HYDRADB_BASE_URL=https://api.hydradb.com
```

Create tenant per [HydraDB quickstart](https://docs.hydradb.com/quickstart).

## Dify console checklist

1. Workflow START inputs: names above (Paragraph for long fields).  
2. LLM: variables inserted with **`/`**, not typed `{{...}}`.  
3. Publish → copy Workflow API key.  
4. Optional: End node outputs (e.g. `text`) appear in `dify_output_preview` on `/api/analyze` response.

## React UI

Run `npm run dev` in `frontend/`; Vite proxies `/api` to the backend. Any other HTTP client can use the same REST API.

Restart **uvicorn** after `.env` changes so environment variables reload.
