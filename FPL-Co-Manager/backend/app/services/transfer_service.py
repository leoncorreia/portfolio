"""Transfer suggestions: position-matched swaps, budget, 3-per-club cap."""

from __future__ import annotations

from collections import Counter

import httpx

from app.providers.fpl_public_api import FPLPublicApiProvider
from app.schemas import Player, RiskProfile, TransferOption
from app.services.scoring_service import ScoringService
from app.utils.fpl_mapping import element_to_player


class TransferService:
    def __init__(self, fpl: FPLPublicApiProvider, scoring: ScoringService) -> None:
        self._fpl = fpl
        self._scoring = scoring

    def _club_counts(self, players: list[Player]) -> Counter[int]:
        return Counter(p.team_id for p in players)

    async def suggest_transfers(
        self,
        squad: list[Player],
        risk: RiskProfile,
        bank: float,
        free_transfers: int,
        max_options: int = 3,
    ) -> tuple[list[TransferOption], str]:
        """
        Returns ranked transfer options and recommended action hint ('roll' or 'transfer').
        Uses full player pool from bootstrap minus current squad IDs.
        """
        if free_transfers < 1:
            return [], "roll"

        try:
            bootstrap = await self._fpl.fetch_bootstrap()
        except httpx.HTTPError:
            return [], "roll"

        squad_ids = {p.id for p in squad}
        candidates: list[Player] = []
        for el in bootstrap.elements_by_id.values():
            pid = int(el["id"])
            if pid in squad_ids:
                continue
            candidates.append(element_to_player(el, bootstrap.teams_by_id))

        options: list[TransferOption] = []
        base_scores = {p.id: self._scoring.projected_points(p, risk) for p in squad}

        for out in squad:
            sell = out.price
            budget_available = bank + sell
            for inc in candidates:
                if inc.position != out.position:
                    continue
                if inc.team_id == out.team_id and inc.id == out.id:
                    continue
                # Price: must be able to afford (FPL uses 0.1m steps)
                if inc.price > budget_available + 0.01:
                    continue
                # Build hypothetical squad swap
                new_squad = [p for p in squad if p.id != out.id] + [inc]
                counts = self._club_counts(new_squad)
                if any(c > 3 for c in counts.values()):
                    continue

                gain = self._scoring.projected_points(inc, risk) - base_scores[out.id]
                cost_delta = inc.price - sell
                reason = (
                    f"+{gain:.2f} projected vs {out.web_name}; "
                    f"cost Δ £{cost_delta:.1f}m; {inc.web_name} ({inc.team_short}) form {inc.form}"
                )
                options.append(
                    TransferOption(
                        player_out_id=out.id,
                        player_out_name=out.web_name,
                        player_in_id=inc.id,
                        player_in_name=inc.web_name,
                        player_in_team=inc.team_short,
                        cost_delta=round(cost_delta, 2),
                        projected_gain=round(gain, 3),
                        reason=reason,
                    )
                )

        options.sort(key=lambda x: x.projected_gain, reverse=True)
        top = options[:max_options]

        # Roll if best gain below threshold
        threshold = 0.25 if risk == "safe" else (0.15 if risk == "balanced" else 0.1)
        action = "roll"
        if top and top[0].projected_gain >= threshold:
            action = "transfer"

        return top, action
