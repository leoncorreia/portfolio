"""
Multimodal image parsing — Kimi vision via GMI (`KIMI_VISION_MODEL`), then JSON extraction.

TODO: Stricter JSON schema validation / squad mapping from model output.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import cast

from app.config import Settings, get_settings
from app.providers.ai_credentials import is_live_key
from app.providers.kimi_provider import kimi_vision_via_gmi
from app.schemas import Player, PositionCode, RiskProfile, Squad


class ImageParserProvider(ABC):
    @abstractmethod
    async def parse_squad_image(self, file_bytes: bytes, content_type: str) -> tuple[Squad | None, str]:
        """Return parsed squad and raw/debug string."""


class StubImageParserProvider(ImageParserProvider):
    async def parse_squad_image(self, file_bytes: bytes, content_type: str) -> tuple[Squad | None, str]:
        msg = (
            f"Stub image parser: received {len(file_bytes)} bytes, type={content_type}. "
            "Set GMI_API_KEY and KIMI_VISION_MODEL for vision parsing (Kimi via GMI)."
        )
        return None, msg


class KimiImageParserProvider(ImageParserProvider):
    """Uses Kimi multimodal chat to describe image; attempts JSON squad extraction."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def parse_squad_image(self, file_bytes: bytes, content_type: str) -> tuple[Squad | None, str]:
        if not is_live_key(self._settings.gmi_api_key):
            stub = StubImageParserProvider()
            return await stub.parse_squad_image(file_bytes, content_type)

        prompt = (
            "This image may show a Fantasy Premier League squad or player list. "
            "If you can infer player names, output ONLY valid JSON with this shape and no markdown:\n"
            '{"players":[{"id":0,"web_name":"Surname","team_id":1,"team_short":"ARS","position":"MID",'
            '"price":6.5,"form":5.0,"minutes":1000,"total_points":40,"points_per_game":4.0,'
            '"ict_index":20.0,"selected_by_percent":10.0,"injury_risk":0.1,"expected_minutes_next":80.0,'
            '"fixture_score":5.0,"ceiling":5.0,"news":"","status":"a"}],'
            '"free_transfers":1,"bank":0.0,"risk_profile":"balanced"}\n'
            "Use real FPL-style positions: GKP, DEF, MID, FWD. If unsure, return empty players array."
        )
        try:
            raw = await kimi_vision_via_gmi(
                self._settings,
                image_bytes=file_bytes,
                mime=content_type or "image/png",
                prompt=prompt,
            )
        except Exception as e:
            return None, f"Kimi vision error: {e}"

        squad = _try_parse_squad_json(raw)
        if squad and squad.players:
            return squad, raw
        return None, raw


def _try_parse_squad_json(text: str) -> Squad | None:
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
        if m:
            t = m.group(1).strip()
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        m2 = re.search(r"\{[\s\S]*\}", t)
        if not m2:
            return None
        try:
            data = json.loads(m2.group(0))
        except json.JSONDecodeError:
            return None

    players_raw = data.get("players") or []
    players: list[Player] = []
    for p in players_raw:
        if not isinstance(p, dict):
            continue
        try:
            pos_raw = str(p.get("position", "MID")).upper()
            if pos_raw not in ("GKP", "DEF", "MID", "FWD"):
                pos_raw = "MID"
            position = cast(PositionCode, pos_raw)
            players.append(
                Player(
                    id=int(p.get("id") or 0),
                    web_name=str(p.get("web_name") or "Unknown"),
                    team_id=int(p.get("team_id") or 0),
                    team_short=str(p.get("team_short") or ""),
                    position=position,
                    price=float(p.get("price") or 0),
                    total_points=int(p.get("total_points") or 0),
                    form=float(p.get("form") or 0),
                    minutes=int(p.get("minutes") or 0),
                    points_per_game=float(p.get("points_per_game") or 0),
                    ict_index=float(p.get("ict_index") or 0),
                    selected_by_percent=float(p.get("selected_by_percent") or 0),
                    injury_risk=float(p.get("injury_risk") or 0),
                    expected_minutes_next=float(p.get("expected_minutes_next") or 70),
                    fixture_score=float(p.get("fixture_score") or 5),
                    ceiling=float(p.get("ceiling") or 5),
                    news=str(p.get("news") or ""),
                    status=str(p.get("status") or "a"),
                )
            )
        except Exception:
            continue

    if not players:
        return None

    rp_raw = str(data.get("risk_profile", "balanced")).lower()
    risk: RiskProfile = "balanced"
    if rp_raw in ("safe", "balanced", "aggressive"):
        risk = cast(RiskProfile, rp_raw)

    return Squad(
        players=players,
        free_transfers=int(data.get("free_transfers", 1)),
        bank=float(data.get("bank", 0.0)),
        risk_profile=risk,
    )
