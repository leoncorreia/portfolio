"""
HydraDB — structured FPL session write + read (latest per user_id).

Uses add_memory + full_recall; parses stored JSON blobs (type fpl_comanager_session).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx

from app.config import Settings
from app.providers.ai_credentials import is_live_key


class HydraMemoryClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = settings.hydradb_base_url.rstrip("/")

    def enabled(self) -> bool:
        return is_live_key(self._settings.hydradb_api_key) and bool(
            (self._settings.hydradb_tenant_id or "").strip()
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.hydradb_api_key}",
            "Content-Type": "application/json",
        }

    async def save_fpl_session(
        self,
        *,
        user_id: str,
        squad_snapshot: dict[str, Any],
        recommendation: dict[str, Any],
        captain_id: int | None,
        transfer_action: str | None,
        transfer_options: list[dict[str, Any]],
    ) -> None:
        if not self.enabled():
            return

        structured = {
            "type": "fpl_comanager_session",
            "user_id": user_id,
            "stored_at": datetime.utcnow().isoformat() + "Z",
            "squad_snapshot": squad_snapshot,
            "recommendation": recommendation,
            "captain_id": captain_id,
            "vice_captain_id": recommendation.get("vice_captain"),
            "transfer_action": transfer_action,
            "transfer_options": transfer_options[:5],
        }
        text = json.dumps(structured, ensure_ascii=False)

        url = f"{self._base}/memories/add_memory"
        body = {
            "tenant_id": self._settings.hydradb_tenant_id,
            "sub_tenant_id": user_id[:128],
            "memories": [
                {
                    "text": text,
                    "infer": self._settings.hydradb_infer_on_write,
                    "title": f"FPL session {user_id}",
                }
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=self._headers(), json=body)
            r.raise_for_status()

    async def load_latest_fpl_session(self, *, user_id: str) -> dict[str, Any] | None:
        """
        Best-effort: recall memories for this user and return the newest fpl_comanager_session JSON.
        """
        if not self.enabled():
            return None

        url = f"{self._base}/recall/full_recall"
        body = {
            "tenant_id": self._settings.hydradb_tenant_id,
            "query": (
                f"fpl_comanager_session user_id {user_id} Fantasy Premier League "
                "recommendation captain transfer"
            ),
            "max_results": self._settings.hydradb_max_results,
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(url, headers=self._headers(), json=body)
                r.raise_for_status()
                data = r.json()
        except Exception:
            return None

        chunks = data.get("chunks") or []
        candidates: list[tuple[str | None, dict[str, Any]]] = []

        for c in chunks:
            raw = c.get("chunk_content") or c.get("content")
            if not raw or not isinstance(raw, str):
                continue
            raw = raw.strip()
            if not raw.startswith("{"):
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "fpl_comanager_session":
                continue
            if str(obj.get("user_id")) != str(user_id):
                continue
            ts = obj.get("stored_at") or c.get("source_upload_time")
            candidates.append((ts if isinstance(ts, str) else None, obj))

        if not candidates:
            return None

        def sort_key(item: tuple[str | None, dict[str, Any]]) -> str:
            return item[0] or ""

        candidates.sort(key=sort_key, reverse=True)
        return candidates[0][1]


def get_hydra_client(settings: Settings) -> HydraMemoryClient | None:
    c = HydraMemoryClient(settings)
    return c if c.enabled() else None
