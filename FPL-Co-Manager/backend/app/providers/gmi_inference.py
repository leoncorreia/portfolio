"""
GMI Cloud — single OpenAI-compatible inference transport (`/v1/chat/completions`).

Kimi models are invoked by passing `KIMI_MODEL` / `KIMI_VISION_MODEL` as the `model` field;
this module does not choose “which LLM” — callers pass the model id.

Docs: https://docs.gmicloud.ai/inference-engine/api-reference
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import Settings
from app.providers.ai_credentials import is_live_key


async def gmi_chat_completion(
    settings: Settings,
    messages: list[dict[str, Any]],
    *,
    model: str,
    max_tokens: int = 2048,
    temperature: float = 0.35,
) -> str:
    """Bearer auth to GMI; returns assistant text content."""
    if not is_live_key(settings.gmi_api_key):
        raise RuntimeError("GMI_API_KEY not configured")

    base = settings.gmi_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.gmi_api_key}",
        "Content-Type": "application/json",
    }
    if settings.gmi_organization_id:
        headers["X-Organization-ID"] = settings.gmi_organization_id

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    choices = data.get("choices") or []
    if not choices:
        return json.dumps(data)[:2000]
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    return str(content)
