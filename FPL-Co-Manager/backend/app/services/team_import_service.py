"""Import FPL squad from public API into normalized Squad."""

from __future__ import annotations

import httpx

from app.providers.fpl_public_api import BootstrapData, FPLPublicApiProvider
from app.schemas import Player, RiskProfile, Squad, TeamImportResponse
from app.utils.fpl_mapping import element_to_player


class TeamImportService:
    def __init__(self, fpl: FPLPublicApiProvider) -> None:
        self._fpl = fpl

    async def import_team(
        self,
        team_id: int,
        free_transfers: int,
        bank: float,
        risk_profile: RiskProfile,
    ) -> TeamImportResponse:
        notes: list[str] = []
        try:
            bootstrap = await self._fpl.fetch_bootstrap()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch FPL bootstrap data: {e}") from e

        try:
            entry = await self._fpl.fetch_entry(team_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Team ID {team_id} not found.") from e
            raise ValueError(f"Failed to fetch entry: {e}") from e
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch entry: {e}") from e

        manager_name = f"{entry.get('player_first_name', '')} {entry.get('player_last_name', '')}".strip()
        team_name = str(entry.get("name") or "Unknown Team")

        try:
            picks_data, pick_notes = await self._fpl.resolve_picks_for_squad(team_id, bootstrap)
        except ValueError as e:
            raise ValueError(str(e)) from e
        notes.extend(pick_notes)

        picks = picks_data.get("picks") or []
        if not picks:
            raise ValueError("No players in squad picks.")

        players: list[Player] = []
        missing: list[str] = []
        for p in picks:
            pid = int(p.get("element"))
            el = bootstrap.elements_by_id.get(pid)
            if el is None:
                missing.append(str(pid))
                continue
            players.append(element_to_player(el, bootstrap.teams_by_id))

        if missing:
            notes.append(f"Skipped unknown player IDs: {', '.join(missing[:10])}")

        if len(players) < 11:
            raise ValueError(f"Too few players resolved ({len(players)}). Check team ID and API availability.")

        # FPL squads are 15 players; if partial, still return what we have with warning
        if len(players) < 15:
            notes.append(
                f"Only {len(players)} players resolved (expected 15). "
                "Analysis may be limited; try again later or use manual entry."
            )

        gw = picks_data.get("event") or bootstrap.current_event
        squad = Squad(
            players=players,
            free_transfers=free_transfers,
            bank=bank,
            risk_profile=risk_profile,
            gameweek=gw,
            team_id=team_id,
        )

        notes.append(
            "Squad source: latest available gameweek picks from public API "
            "(may be previous GW if current picks are not published yet)."
        )

        return TeamImportResponse(
            manager_name=manager_name,
            team_name=team_name,
            squad=squad,
            import_notes=notes,
        )
