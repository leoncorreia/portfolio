"""
Kimi — explanation + multimodal parsing only, always via GMI inference endpoint.

Lineup, transfers, and scoring remain in services (deterministic).
"""

from __future__ import annotations

import base64
from typing import Any

from app.config import Settings, get_settings
from app.providers.ai_credentials import is_live_key
from app.providers.explanation_provider import ExplanationProvider
from app.providers.gmi_inference import gmi_chat_completion
from app.schemas import Recommendation, Squad


class StubExplanationProvider(ExplanationProvider):
    """When GMI is not configured or call fails at the service boundary."""

    async def generate_explanation(
        self,
        squad: Squad,
        recommendation: Recommendation,
        *,
        user_id: str,
        deterministic_explanation: str,
    ) -> str:
        return (
            "Configure GMI_API_KEY, GMI_BASE_URL, and KIMI_MODEL for coach-style explanations "
            "(Kimi hosted on GMI). "
            f"Formation {recommendation.formation or 'n/a'}; transfer: {recommendation.transfer_action}."
        )


class KimiViaGMIProvider(ExplanationProvider):
    """Kimi model id + GMI `/v1/chat/completions` — one path, no fallbacks."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def generate_explanation(
        self,
        squad: Squad,
        recommendation: Recommendation,
        *,
        user_id: str,
        deterministic_explanation: str,
    ) -> str:
        if not is_live_key(self._settings.gmi_api_key):
            stub = StubExplanationProvider()
            return await stub.generate_explanation(
                squad, recommendation, user_id=user_id, deterministic_explanation=deterministic_explanation
            )

        system = (
            "You are an expert Fantasy Premier League co-manager. "
            "Write a concise, actionable explanation for the manager. "
            "Do not contradict the structured recommendation JSON; you may clarify and motivate."
        )
        user_msg = (
            f"user_id: {user_id}\n\n"
            f"Deterministic analysis (source of truth for decisions):\n{deterministic_explanation}\n\n"
            f"Squad JSON:\n{squad.model_dump_json()}\n\n"
            f"Recommendation JSON:\n{recommendation.model_dump_json()}"
        )
        try:
            return await gmi_chat_completion(
                self._settings,
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                model=self._settings.kimi_model,
            )
        except Exception as e:
            return f"[Explanation unavailable: {e}]"


async def kimi_vision_via_gmi(
    settings: Settings,
    *,
    image_bytes: bytes,
    mime: str,
    prompt: str,
) -> str:
    """Multimodal parse — same GMI endpoint, vision model id from settings."""
    if not is_live_key(settings.gmi_api_key):
        raise RuntimeError("GMI_API_KEY not configured")

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    return await gmi_chat_completion(
        settings,
        messages,
        model=settings.kimi_vision_model,
    )

