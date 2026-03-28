"""Human-readable explanation strings from structured recommendation."""

from __future__ import annotations

from app.schemas import Player, Recommendation, Squad


class ExplanationService:
    def build(self, squad: Squad, rec: Recommendation, players_by_id: dict[int, Player]) -> str:
        lines: list[str] = []
        lines.append(
            f"Formation {rec.formation} maximizes combined projected output under your "
            f"{squad.risk_profile} risk profile."
        )
        cap = players_by_id.get(rec.captain) if rec.captain else None
        vice = players_by_id.get(rec.vice_captain) if rec.vice_captain else None
        if cap:
            lines.append(f"Captain: {cap.web_name} — strong fixture and minutes profile.")
        if vice:
            lines.append(f"Vice-captain: {vice.web_name}.")
        if rec.transfer_action == "roll":
            lines.append("Transfers: rolling is sensible; no swap clears the gain threshold.")
        else:
            lines.append("Transfers: at least one swap shows meaningful projected gain.")
            for i, t in enumerate(rec.transfer_options[:3], 1):
                lines.append(f"  {i}. {t.player_out_name} → {t.player_in_name}: {t.reason}")
        lines.append(rec.summary)
        return "\n".join(lines)
