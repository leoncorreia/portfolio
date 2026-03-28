"""Orchestrates deterministic scoring + single-path Kimi explanation (via GMI)."""

from __future__ import annotations

from app.providers.explanation_provider import ExplanationProvider
from app.providers.kimi_provider import KimiViaGMIProvider
from app.schemas import Recommendation, Squad
from app.services.explanation_service import ExplanationService
from app.services.optimizer_service import OptimizerService
from app.services.scoring_service import ScoringService
from app.services.transfer_service import TransferService


class RecommendationService:
    def __init__(
        self,
        scoring: ScoringService,
        optimizer: OptimizerService,
        transfers: TransferService,
        explanation: ExplanationService,
        kimi_explanation: ExplanationProvider | None = None,
    ) -> None:
        self._scoring = scoring
        self._optimizer = optimizer
        self._transfers = transfers
        self._explanation = explanation
        self._kimi_explanation = kimi_explanation or KimiViaGMIProvider()

    async def analyze(self, squad: Squad, *, user_id: str = "local") -> Recommendation:
        players = squad.players
        by_id = {p.id: p for p in players}
        risk = squad.risk_profile

        lineup = self._optimizer.best_lineup(players, risk)
        starting_players = [by_id[i] for i in lineup.starting_ids if i in by_id]
        cap_id, vice_id = self._optimizer.pick_captain_vice(starting_players, risk)

        transfer_opts, action = await self._transfers.suggest_transfers(
            players,
            risk,
            squad.bank,
            squad.free_transfers,
            max_options=3,
        )

        summary_parts = [
            f"Projected best XI ({lineup.formation}).",
            f"Bank £{squad.bank:.1f}m, free transfers: {squad.free_transfers}.",
        ]
        summary = " ".join(summary_parts)

        rec = Recommendation(
            summary=summary,
            starting_xi=lineup.starting_ids,
            bench_order=lineup.bench_ids,
            captain=cap_id,
            vice_captain=vice_id,
            transfer_action=action,  # type: ignore[arg-type]
            transfer_options=transfer_opts,
            explanation="",
            confidence="medium" if len(players) >= 14 else "low",
            formation=lineup.formation,
        )

        deterministic_text = self._explanation.build(squad, rec, by_id)
        coach_text = await self._kimi_explanation.generate_explanation(
            squad,
            rec,
            user_id=user_id,
            deterministic_explanation=deterministic_text,
        )
        rec.explanation = deterministic_text + "\n\n--- Coach explanation (Kimi via GMI) ---\n\n" + coach_text

        return rec
