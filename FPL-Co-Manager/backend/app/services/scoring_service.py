"""
Deterministic player scoring. Tune weights here.

Default projection:
  0.35 * RecentForm + 0.25 * FixtureScore + 0.20 * ExpectedMinutes
  + 0.15 * UnderlyingStats - 0.20 * InjuryRisk + position_bonus

Risk profiles adjust multipliers:
- safe: more minutes, more injury penalty
- balanced: baseline
- aggressive: more ceiling in projection

Captain score:
  0.45 * ProjectionNext1 + 0.25 * ExpectedMinutes + 0.20 * FixtureScore + 0.10 * CeilingScore
"""

from __future__ import annotations

from app.schemas import Player, RiskProfile


def _norm_form(p: Player) -> float:
    # Form is typically 0-10+ ; cap for stability
    return min(10.0, max(0.0, float(p.form)))


def _norm_minutes_exp(p: Player) -> float:
    return min(10.0, max(0.0, p.expected_minutes_next / 9.0))


def _underlying(p: Player) -> float:
    ppg = min(5.0, max(0.0, p.points_per_game))
    ict = min(10.0, max(0.0, p.ict_index / 30.0))
    return min(10.0, ppg * 1.4 + ict * 0.6)


def _position_bonus(p: Player) -> float:
    return {"GKP": 0.2, "DEF": 0.4, "MID": 0.5, "FWD": 0.6}.get(p.position, 0.0)


class ScoringService:
    def __init__(self) -> None:
        # Base weights (balanced)
        self.w_form = 0.35
        self.w_fixture = 0.25
        self.w_minutes = 0.20
        self.w_underlying = 0.15
        self.w_injury = 0.20
        self.w_ceiling = 0.15  # used in aggressive blend

    def projected_points(self, p: Player, risk: RiskProfile) -> float:
        form = _norm_form(p)
        fix = min(10.0, max(0.0, p.fixture_score))
        mins = _norm_minutes_exp(p)
        und = _underlying(p)
        inj = min(1.0, max(0.0, p.injury_risk))
        ceil = min(10.0, max(0.0, p.ceiling))
        pos = _position_bonus(p)

        if risk == "safe":
            w_form, w_fix, w_mins, w_und, w_inj, w_ceil = (
                0.30,
                0.22,
                0.28,
                0.12,
                0.32,
                0.05,
            )
        elif risk == "aggressive":
            w_form, w_fix, w_mins, w_und, w_inj, w_ceil = (
                0.32,
                0.22,
                0.16,
                0.12,
                0.15,
                0.28,
            )
        else:
            w_form = self.w_form
            w_fix = self.w_fixture
            w_mins = self.w_minutes
            w_und = self.w_underlying
            w_inj = self.w_injury
            w_ceil = self.w_ceiling

        base = (
            w_form * form
            + w_fix * fix
            + w_mins * mins
            + w_und * und
            - w_inj * inj * 10.0
            + w_ceil * ceil
            + pos
        )
        return round(base, 3)

    def captain_score(self, p: Player, risk: RiskProfile) -> float:
        proj = self.projected_points(p, risk)
        mins = _norm_minutes_exp(p)
        fix = min(10.0, max(0.0, p.fixture_score))
        ceil = min(10.0, max(0.0, p.ceiling))
        return round(
            0.45 * proj
            + 0.25 * mins * 10.0 / 9.0
            + 0.20 * fix
            + 0.10 * ceil,
            3,
        )
