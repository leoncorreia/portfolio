"""
Validate KIMI_MODEL / KIMI_VISION_MODEL against GET {GMI_BASE_URL}/models.

OpenAI-style request body for chat completions:
  POST {base}/chat/completions
  { "model": "<id>", "messages": [...], "max_tokens", "temperature" }

Model ids must match an entry returned by the models list (exact string match).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings
from app.providers.ai_credentials import is_live_key

logger = logging.getLogger(__name__)


def _collect_model_ids(payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for item in payload.get("data") or []:
        if not isinstance(item, dict):
            continue
        for key in ("id", "object"):
            v = item.get(key)
            if isinstance(v, str) and v.strip():
                ids.add(v.strip())
    return ids


async def fetch_gmi_model_ids(settings: Settings) -> set[str]:
    if not is_live_key(settings.gmi_api_key):
        return set()
    base = settings.gmi_base_url.rstrip("/")
    url = f"{base}/models"
    headers: dict[str, str] = {"Authorization": f"Bearer {settings.gmi_api_key}"}
    if settings.gmi_organization_id:
        headers["X-Organization-ID"] = settings.gmi_organization_id
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return _collect_model_ids(r.json())


async def validate_gmi_kimi_models(settings: Settings) -> list[str]:
    """
    Returns human-readable issues (empty if ok or validation skipped).
    Does not raise — logs warnings for demo reliability.
    """
    issues: list[str] = []
    if not is_live_key(settings.gmi_api_key):
        issues.append("GMI_API_KEY not set — skipping model list validation.")
        return issues
    try:
        available = await fetch_gmi_model_ids(settings)
    except Exception as e:
        issues.append(f"Could not fetch GMI /models: {e}")
        return issues

    if not available:
        issues.append("GMI /models returned no model ids — check API key and base URL.")
        return issues

    for label, mid in (
        ("KIMI_MODEL", settings.kimi_model),
        ("KIMI_VISION_MODEL", settings.kimi_vision_model),
    ):
        if mid not in available:
            sample = sorted(available)[:12]
            issues.append(
                f"{label}={mid!r} not found in GMI catalog. "
                f"First ids from account: {sample!r} (exact match required)."
            )
        else:
            logger.info("GMI model OK: %s=%s", label, mid)

    return issues
