# FPL AI Co-Manager — Frontend

React + Vite + TypeScript UI for importing an FPL team, analyzing, and viewing recommendations + memory.

**Photon** in your stack means **[Photon Spectrum](https://photon.codes/spectrum)** (agent ↔ Telegram, WhatsApp, iMessage, etc.). That is **not** this web bundle: Spectrum would sit beside or behind the FastAPI service if you add channel bots later. The header links to Spectrum for context.

## Setup

```bash
cd frontend
npm install
npm run dev
```

**Windows:** from `frontend/`, `.\run-dev.ps1` stops stray listeners on **5173–5176** then starts Vite so you always get **one** UI at [http://127.0.0.1:5173](http://127.0.0.1:5173) (Vite is configured with `strictPort: true` so it will not auto-bump to 5174 if 5173 is busy — free the port or stop the other process first).

By default Vite proxies `/api` and `/health` to `http://127.0.0.1:8000`. If the API uses another port (e.g. 8001 after a bind conflict), set `VITE_DEV_PROXY_TARGET` in `frontend/.env` to that origin (see `.env.example`).

## Scripts

- `npm run dev` — dev server at [http://127.0.0.1:5173](http://127.0.0.1:5173) (host/port fixed in `vite.config.ts`)
- `run-dev.ps1` — Windows helper: clear 5173–5176, then `npm run dev`
- `npm run build` — production bundle to `dist/`
- `npm run preview` — preview production build

## Structure

| Path | Role |
|------|------|
| `src/App.tsx` | Main flow: import → analyze → results |
| `src/components/` | UI cards and layout |
| `src/services/api.ts` | HTTP client |
| `src/types.ts` | Shared TypeScript types |
| `src/hooks/useStableUserId.ts` | Persists `user_id` in `localStorage` for memory APIs |

## Optional env

See `.env.example`. For production you may set `VITE_API_URL` and change `api.ts` to prefix requests — the dev setup uses the Vite proxy instead.
