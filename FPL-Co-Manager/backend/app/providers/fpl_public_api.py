"""
Fantasy Premier League public HTTP API.

Uses official-style endpoints under FPL_BASE_URL (default: fantasy.premierleague.com/api).

Assumption (documented): "Current" squad is taken from the latest completed gameweek picks
if the current-event picks endpoint is not yet available for the live GW, or from
entry/{id}/event/{current_event}/picks/ when the API returns data for that event.
We try current_event first, then fall back to previous event from bootstrap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import Settings


ELEMENT_TYPE_TO_POS = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}


@dataclass
class BootstrapData:
    """Parsed bootstrap-static payload."""

    elements_by_id: dict[int, dict[str, Any]]
    teams_by_id: dict[int, dict[str, Any]]
    current_event: int | None
    raw: dict[str, Any] = field(default_factory=dict)


class FPLPublicApiProvider:
    def __init__(self, settings: Settings) -> None:
        self._base = settings.fpl_base_url.rstrip("/")

    async def fetch_bootstrap(self) -> BootstrapData:
        url = f"{self._base}/bootstrap-static/"
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

        elements = {el["id"]: el for el in data.get("elements", [])}
        teams = {t["id"]: t for t in data.get("teams", [])}
        current_event: int | None = None
        for ev in data.get("events", []):
            if ev.get("is_current"):
                current_event = ev.get("id")
                break
        if current_event is None and data.get("events"):
            # Fallback: max id where finished or first upcoming
            for ev in sorted(data["events"], key=lambda x: x.get("id", 0)):
                if ev.get("is_next"):
                    current_event = ev.get("id")
                    break

        return BootstrapData(
            elements_by_id=elements,
            teams_by_id=teams,
            current_event=current_event,
            raw=data,
        )

    async def fetch_entry(self, team_id: int) -> dict[str, Any]:
        url = f"{self._base}/entry/{team_id}/"
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()

    async def fetch_picks(self, team_id: int, event_id: int) -> dict[str, Any]:
        url = f"{self._base}/entry/{team_id}/event/{event_id}/picks/"
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json()

    async def resolve_picks_for_squad(
        self, team_id: int, bootstrap: BootstrapData
    ) -> tuple[dict[str, Any], list[str]]:
        """
        Return picks payload and notes. Tries current GW from entry, then bootstrap current_event,
        then previous event id.
        """
        notes: list[str] = []
        entry = await self.fetch_entry(team_id)
        current = entry.get("current_event") or bootstrap.current_event

        async def try_event(eid: int | None) -> dict[str, Any] | None:
            if eid is None:
                return None
            try:
                return await self.fetch_picks(team_id, eid)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    notes.append(f"Picks for event {eid} not found (404).")
                    return None
                raise

        picks = await try_event(current)
        if picks is None and bootstrap.raw.get("events"):
            events_sorted = sorted(bootstrap.raw["events"], key=lambda x: -x.get("id", 0))
            for ev in events_sorted[:5]:
                eid = ev.get("id")
                picks = await try_event(eid)
                if picks is not None:
                    notes.append(f"Using picks from gameweek {eid} (fallback).")
                    break

        if picks is None:
            raise ValueError("Could not load squad picks for any recent gameweek.")

        return picks, notes
