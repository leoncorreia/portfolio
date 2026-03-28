"""
Legal formation search over 15-player squad.

Valid FPL outfield shapes (DEF-MID-FWD) with GKP 1:
3-4-3, 3-5-2, 4-4-2, 4-3-3, 4-5-1, 5-3-2, 5-4-1
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas import Player, RiskProfile
from app.services.scoring_service import ScoringService

VALID_FORMATIONS: list[tuple[int, int, int]] = [
    (3, 4, 3),
    (3, 5, 2),
    (4, 4, 2),
    (4, 3, 3),
    (4, 5, 1),
    (5, 3, 2),
    (5, 4, 1),
]


@dataclass
class LineupResult:
    formation: str
    starting_ids: list[int]
    bench_ids: list[int]
    total_score: float


class OptimizerService:
    def __init__(self, scoring: ScoringService) -> None:
        self._scoring = scoring

    def _by_pos(self, players: list[Player], risk: RiskProfile) -> dict[str, list[Player]]:
        out: dict[str, list[Player]] = {"GKP": [], "DEF": [], "MID": [], "FWD": []}
        for p in players:
            out[p.position].append(p)
        for k in out:
            out[k].sort(key=lambda x: self._scoring.projected_points(x, risk), reverse=True)
        return out

    def best_lineup(self, players: list[Player], risk: RiskProfile) -> LineupResult:
        if len(players) < 15:
            # Pad logic: still optimize best 11 from available
            pass
        by_pos = self._by_pos(players, risk)
        gkps = by_pos["GKP"]
        defs_ = by_pos["DEF"]
        mids = by_pos["MID"]
        fwds = by_pos["FWD"]

        best: LineupResult | None = None

        for d, m, f in VALID_FORMATIONS:
            if len(defs_) < d or len(mids) < m or len(fwds) < f or len(gkps) < 1:
                continue
            starters: list[Player] = []
            starters.append(gkps[0])
            starters.extend(defs_[:d])
            starters.extend(mids[:m])
            starters.extend(fwds[:f])
            if len(starters) != 11:
                continue
            total = sum(self._scoring.projected_points(p, risk) for p in starters)
            ids = [p.id for p in starters]
            used = set(ids)
            bench = [p for p in players if p.id not in used]
            bench.sort(key=lambda x: self._scoring.projected_points(x, risk), reverse=True)
            if best is None or total > best.total_score:
                best = LineupResult(
                    formation=f"{d}-{m}-{f}",
                    starting_ids=ids,
                    bench_ids=[p.id for p in bench[:4]],
                    total_score=total,
                )

        if best is None:
            # Fallback: take top 11 by score ignoring formation (invalid for real FPL)
            all_sorted = sorted(
                players,
                key=lambda x: self._scoring.projected_points(x, risk),
                reverse=True,
            )
            top11 = all_sorted[:11]
            rest = all_sorted[11:]
            return LineupResult(
                formation="custom-fallback",
                starting_ids=[p.id for p in top11],
                bench_ids=[p.id for p in rest[:4]],
                total_score=sum(self._scoring.projected_points(p, risk) for p in top11),
            )

        return best

    def pick_captain_vice(
        self, starting_players: list[Player], risk: RiskProfile
    ) -> tuple[int | None, int | None]:
        if not starting_players:
            return None, None
        ranked = sorted(
            starting_players,
            key=lambda x: self._scoring.captain_score(x, risk),
            reverse=True,
        )
        cap = ranked[0].id
        vice = ranked[1].id if len(ranked) > 1 else None
        return cap, vice
