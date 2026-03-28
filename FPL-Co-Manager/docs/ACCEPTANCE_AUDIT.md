# Acceptance criteria audit (implementation status)

## 1. Dify invoked at runtime

**Status: implemented**

- Every `POST /api/analyze` (via `MemoryService.analyze_with_memory`) ends with `invoke_post_analyze_orchestration` → HTTP `POST {DIFY_BASE_URL}/workflows/run` when `DIFY_API_KEY` is set.
- Response fields: `dify_used`, `dify_error`, `dify_workflow_run_id`, `dify_status`, `dify_output_preview`; main workflow text is also appended under `--- Dify workflow note ---` in `recommendation.explanation`.
- Dify is **not** used to generate the coach text; Kimi via GMI does that.

## 2. HydraDB write + read (latest session)

**Status: implemented (best-effort read)**

- **Write:** `save_fpl_session` after each analyze (structured JSON including `stored_at`).
- **Read:** `load_latest_fpl_session` uses `full_recall`, parses `fpl_comanager_session` chunks for `user_id`, picks newest by `stored_at`.
- **Fallback:** If Hydra returns nothing, `previous_summary` comes from SQLite.
- **Flag:** `previous_from_hydradb` indicates the summary source.

Hydra’s recall API is semantic; “latest” is enforced in app code by sorting parsed blobs, not a native Hydra “get by id” API.

## 3. Kimi via GMI — model ids and request format

**Status: implemented**

- **Transport:** `POST {GMI_BASE_URL}/chat/completions` with JSON body:
  - `model`: `KIMI_MODEL` (text) or `KIMI_VISION_MODEL` (vision messages)
  - `messages`: OpenAI-style chat messages
  - `max_tokens`, `temperature`
- **Auth:** `Authorization: Bearer {GMI_API_KEY}`; optional `X-Organization-ID`.
- **Validation:** On startup, `GET {GMI_BASE_URL}/models` and log warnings if configured model ids are not in the catalog (exact match).

## 4. UI labeling

**Status: corrected in docs**

- The shipped UI is **React + Vite + TypeScript** only (`frontend/`).
- README and integration docs describe it as such; no third-party UI framework name is used as a label for this app.

## 5. Deterministic vs Kimi explanation

**Status: satisfied**

- Lineup, bench, captain, transfers: `optimizer_service`, `transfer_service`, `scoring_service` only.
- `RecommendationService` builds the recommendation, then `KimiViaGMIProvider.generate_explanation` appends narrative; `MemoryService` splits deterministic vs coach text only for Dify inputs.

## 6. GMI as transport only

**Status: satisfied**

- `gmi_inference.gmi_chat_completion` has no provider fallback.
- No alternate “GMI LLM path” beside Kimi model ids.

---

## Stub / partial

| Item | Note |
|------|------|
| `POST /api/compare-last` | Calls `RecommendationService.analyze` only; does **not** trigger Dify/Hydra write path (by design: read-only compare). |
| Dify workflow semantics | App sends inputs; **your** Dify graph defines what happens (webhooks, logging, etc.). |
| Hydra “latest” | Depends on recall quality; may need tuning `HYDRADB_MAX_RESULTS` or query string. |
