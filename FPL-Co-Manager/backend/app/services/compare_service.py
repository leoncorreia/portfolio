"""Compare latest stored recommendation with a fresh analysis on current squad."""

from __future__ import annotations

from app.repositories.interfaces import MemoryRepository
from app.schemas import CompareSummary, Squad
from app.services.recommendation_service import RecommendationService


class CompareService:
    def __init__(self, repo: MemoryRepository, rec: RecommendationService) -> None:
        self._repo = repo
        self._rec = rec

    async def compare_last_vs_current(self, user_id: str, squad: Squad) -> CompareSummary:
        latest = self._repo.get_latest(user_id)
        fresh = await self._rec.analyze(squad, user_id=user_id)

        last_cap = latest.recommendation.get("captain") if latest else None
        last_action = latest.recommendation.get("transfer_action") if latest else None

        narrative_parts: list[str] = []
        if latest is None:
            narrative_parts.append("No prior recommendation stored for this user.")
        else:
            if last_cap != fresh.captain:
                narrative_parts.append(
                    f"Captain changed from prior pick ({last_cap}) to {fresh.captain} based on current projections."
                )
            else:
                narrative_parts.append("Captain choice aligns with your last saved run.")
            if last_action != fresh.transfer_action:
                narrative_parts.append(
                    f"Transfer stance shifted: was '{last_action}', now '{fresh.transfer_action}'."
                )

        return CompareSummary(
            last_captain_id=last_cap if isinstance(last_cap, int) else None,
            current_captain_id=fresh.captain,
            last_transfer_action=str(last_action) if last_action else None,
            current_transfer_action=fresh.transfer_action,
            narrative=" ".join(narrative_parts) if narrative_parts else "Compared current squad to history.",
        )
