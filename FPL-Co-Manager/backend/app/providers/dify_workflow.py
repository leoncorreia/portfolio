"""
Dify — POST {DIFY_BASE_URL}/workflows/run (blocking).

Orchestration / extra narrative only; does not replace deterministic + Kimi explanations.

Reference workflow (START input **names** must match ``DIFY_INPUT_*``):

- ``squad`` — JSON string
- ``recommendation`` — JSON string
- ``deterministic_explanation`` — plain text (not ``deterministic_reasoning``)
- ``user_id`` — string (also sent as top-level API ``user``)

**Dify UI:** In the LLM node, insert variables with the **``/``** menu (variable picker). Typing
``{{squad}}`` by hand usually does **not** bind START inputs, so the model sees empty values.
Optionally set ``DIFY_INPUT_BUNDLE`` and add one Paragraph variable; put only that variable in the
prompt via ``/`` (see README).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.providers.ai_credentials import is_live_key

logger = logging.getLogger(__name__)

_DIFY_NOTE_MARKER = "\n\n--- Dify workflow note ---\n"


def _normalize_dify_string_inputs(
    squad_json: str,
    recommendation_json: str,
    deterministic_explanation: str,
    user_id: str,
) -> tuple[str, str, str, str]:
    """Ensure every workflow input is a non-empty string (Dify START / LLM sees empty as missing)."""
    s = (squad_json or "").strip() or "{}"
    r = (recommendation_json or "").strip() or "{}"
    d = (deterministic_explanation or "").strip() or "(no deterministic segment)"
    u = (user_id or "").strip() or "anonymous"
    return s, r, d, u


def _build_fpl_coaching_bundle(s: str, r: str, d: str, u: str) -> str:
    """Single markdown blob for one Dify START variable (use `/` to insert in the LLM node)."""
    return (
        "### Squad (JSON)\n"
        f"{s}\n\n"
        "### Recommendation (JSON)\n"
        f"{r}\n\n"
        "### Base reasoning (deterministic)\n"
        f"{d}\n\n"
        "### User ID\n"
        f"{u}\n"
    )


def _extract_main_output_text(outputs: Any) -> str:
    """Prefer outputs.answer, then outputs.text; then generic extraction."""
    if outputs is None:
        return ""
    if isinstance(outputs, str):
        return outputs.strip()
    if isinstance(outputs, dict):
        for key in ("answer", "text"):
            if key not in outputs or outputs[key] is None:
                continue
            v = outputs[key]
            if isinstance(v, str):
                return v.strip()
            return json.dumps(v, ensure_ascii=False)[:80000]
        for _k, v in outputs.items():
            if isinstance(v, str) and v.strip():
                return v.strip()
        return json.dumps(outputs, ensure_ascii=False)[:80000]
    return str(outputs)


def _fallback_outputs_text(outputs: Any) -> str:
    if isinstance(outputs, dict):
        for key in ("result", "output", "explanation"):
            if key in outputs and outputs[key] is not None:
                v = outputs[key]
                if isinstance(v, str):
                    return v.strip()
                return json.dumps(v, ensure_ascii=False)[:80000]
    return _extract_main_output_text(outputs)


@dataclass
class DifyWorkflowRunResult:
    skipped: bool
    attempted: bool
    dify_used: bool  # True when POST succeeded and response parsed without fatal error
    workflow_run_id: str | None
    status: str | None
    output_text: str | None  # main text for appending to explanation
    output_preview: str | None  # truncated for JSON response
    error: str | None = None


async def run_dify_workflow_blocking(
    settings: Settings,
    *,
    inputs: dict[str, str],
    user_id: str,
) -> DifyWorkflowRunResult:
    if not is_live_key(settings.dify_api_key):
        logger.info("Dify: skipped (DIFY_API_KEY not set or placeholder)")
        return DifyWorkflowRunResult(
            skipped=True,
            attempted=False,
            dify_used=False,
            workflow_run_id=None,
            status=None,
            output_text=None,
            output_preview=None,
            error=None,
        )

    base = settings.dify_base_url.rstrip("/")
    url = f"{base}/workflows/run"
    headers = {
        "Authorization": f"Bearer {settings.dify_api_key}",
        "Content-Type": "application/json",
    }
    user_str = str(user_id)
    body: dict[str, Any] = {
        "inputs": inputs,
        "response_mode": "blocking",
        "user": user_str,
    }

    timeout = float(settings.dify_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=body)
            raw = r.text
    except httpx.TimeoutException as e:
        logger.warning("Dify: request timeout after %ss — %s", timeout, e)
        return DifyWorkflowRunResult(
            skipped=False,
            attempted=True,
            dify_used=False,
            workflow_run_id=None,
            status=None,
            output_text=None,
            output_preview=None,
            error=f"timeout: {e}",
        )
    except Exception as e:
        logger.warning("Dify: request failed — %s", e)
        return DifyWorkflowRunResult(
            skipped=False,
            attempted=True,
            dify_used=False,
            workflow_run_id=None,
            status=None,
            output_text=None,
            output_preview=None,
            error=str(e),
        )

    if r.status_code >= 400:
        logger.warning("Dify: HTTP %s — body (truncated): %s", r.status_code, raw[:2000])
        return DifyWorkflowRunResult(
            skipped=False,
            attempted=True,
            dify_used=False,
            workflow_run_id=None,
            status=None,
            output_text=None,
            output_preview=None,
            error=f"HTTP {r.status_code}",
        )

    try:
        result = r.json()
    except json.JSONDecodeError:
        logger.warning("Dify: malformed JSON — raw (truncated): %s", raw[:2000])
        return DifyWorkflowRunResult(
            skipped=False,
            attempted=True,
            dify_used=False,
            workflow_run_id=None,
            status=None,
            output_text=None,
            output_preview=None,
            error="Dify returned non-JSON body",
        )

    run_id = result.get("workflow_run_id") or result.get("id")
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, dict):
        data = result if isinstance(result, dict) else {}

    status = data.get("status")
    outputs = data.get("outputs")
    inner = data.get("data")
    if outputs is None and isinstance(inner, dict):
        outputs = inner.get("outputs")
        status = status or inner.get("status")

    main_text = _extract_main_output_text(outputs)
    if not main_text and outputs is not None:
        main_text = _fallback_outputs_text(outputs)

    err: str | None = None
    if status == "failed":
        err = "workflow status failed"

    status_str = str(status) if status is not None else None
    dify_ok = err is None and status_str != "failed"

    preview = (main_text[:2000] + "…") if len(main_text) > 2000 else main_text if main_text else None

    if dify_ok:
        logger.info(
            "Dify: workflow OK run_id=%s status=%s text_len=%s",
            run_id,
            status_str,
            len(main_text),
        )
    else:
        logger.warning("Dify: workflow incomplete status=%s error=%s", status_str, err)

    return DifyWorkflowRunResult(
        skipped=False,
        attempted=True,
        dify_used=dify_ok,
        workflow_run_id=str(run_id) if run_id else None,
        status=status_str,
        output_text=main_text if main_text else None,
        output_preview=preview,
        error=err,
    )


async def invoke_post_analyze_orchestration(
    settings: Settings,
    *,
    user_id: str,
    squad_json: str,
    recommendation_json: str,
    deterministic_explanation: str,
) -> DifyWorkflowRunResult:
    """Build inputs using env-configured START variable names (string values only).

    Keys follow ``DIFY_INPUT_*`` env vars. In Dify, wire the LLM with the **``/``** variable
    picker (not hand-typed ``{{...}}``). If ``DIFY_INPUT_BUNDLE`` is set, that key receives a
    single markdown block with all sections (convenient for one ``/`` insert).
    """
    s, r, d, u = _normalize_dify_string_inputs(
        squad_json, recommendation_json, deterministic_explanation, user_id
    )
    inputs: dict[str, str] = {
        settings.dify_input_squad: s,
        settings.dify_input_recommendation: r,
        settings.dify_input_deterministic: d,
        settings.dify_input_user_id: u,
    }
    bundle_key = (settings.dify_input_bundle or "").strip()
    if bundle_key:
        inputs[bundle_key] = _build_fpl_coaching_bundle(s, r, d, u)
    return await run_dify_workflow_blocking(settings, inputs=inputs, user_id=u)
