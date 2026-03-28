"""Map FPL bootstrap element + team rows to normalized Player fields."""

from __future__ import annotations

from typing import Any

from app.providers.fpl_public_api import ELEMENT_TYPE_TO_POS
from app.schemas import Player, PositionCode


def _injury_risk_from_element(el: dict[str, Any]) -> float:
    status = (el.get("status") or "a").lower()
    if status in ("a", ""):
        base = 0.05
    elif status in ("d",):
        base = 0.35
    else:
        base = 0.65
    ch = el.get("chance_of_playing_next_round")
    if ch is not None:
        base = max(base, (100 - float(ch)) / 100.0)
    return min(1.0, base)


def _expected_minutes(el: dict[str, Any]) -> float:
    mins = int(el.get("minutes") or 0)
    if mins < 90:
        return max(0.0, min(90.0, mins * 0.15 + 45.0))
    # Established regular
    return min(90.0, 75.0 + min(15.0, (mins - 900) / 200.0))


def _fixture_score(team_row: dict[str, Any] | None) -> float:
    if not team_row:
        return 5.0
    # FPL team strength is 1-5; map to 0-10 (higher = easier fixture run heuristic)
    s = float(team_row.get("strength") or 3)
    return min(10.0, max(0.0, s * 2.0))


def _ceiling(el: dict[str, Any]) -> float:
    form = float(el.get("form") or 0)
    ict = float(el.get("ict_index") or 0) / 10.0
    return min(10.0, form * 0.6 + min(5.0, ict) * 0.8)


def element_to_player(el: dict[str, Any], teams_by_id: dict[int, dict[str, Any]]) -> Player:
    et = int(el.get("element_type") or 1)
    pos: PositionCode = ELEMENT_TYPE_TO_POS.get(et, "MID")
    tid = int(el.get("team") or 0)
    team_row = teams_by_id.get(tid)
    short = team_row.get("short_name", "") if team_row else ""
    now_cost = float(el.get("now_cost") or 0) / 10.0

    return Player(
        id=int(el["id"]),
        web_name=str(el.get("web_name") or "Unknown"),
        full_name=f"{el.get('first_name', '')} {el.get('second_name', '')}".strip() or None,
        team_id=tid,
        team_short=short,
        position=pos,
        price=now_cost,
        total_points=int(el.get("total_points") or 0),
        form=float(el.get("form") or 0),
        minutes=int(el.get("minutes") or 0),
        points_per_game=float(el.get("points_per_game") or 0),
        ict_index=float(el.get("ict_index") or 0),
        selected_by_percent=float(el.get("selected_by_percent") or 0),
        injury_risk=_injury_risk_from_element(el),
        expected_minutes_next=_expected_minutes(el),
        fixture_score=_fixture_score(team_row),
        ceiling=_ceiling(el),
        news=str(el.get("news") or ""),
        status=str(el.get("status") or "a"),
    )
