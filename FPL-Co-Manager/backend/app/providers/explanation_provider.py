"""Explanation-only interface — implemented by Kimi (via GMI) or stub."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import Recommendation, Squad


class ExplanationProvider(ABC):
    """Narrative layer only; all lineup/transfer logic stays deterministic elsewhere."""

    @abstractmethod
    async def generate_explanation(
        self,
        squad: Squad,
        recommendation: Recommendation,
        *,
        user_id: str,
        deterministic_explanation: str,
    ) -> str:
        """Single explanation string (no provider fallback inside)."""
