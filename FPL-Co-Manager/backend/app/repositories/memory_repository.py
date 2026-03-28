"""SQLite-backed recommendation history."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import RecommendationHistory
from app.repositories.interfaces import MemoryRepository
from app.schemas import MemoryRecordOut, Recommendation, Squad


def _squad_to_dict(squad: Squad) -> dict[str, Any]:
    return json.loads(squad.model_dump_json())


def _rec_to_dict(rec: Recommendation) -> dict[str, Any]:
    return json.loads(rec.model_dump_json())


class SQLiteMemoryRepository(MemoryRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_recommendation(
        self,
        user_id: str,
        squad: Squad,
        recommendation: Recommendation,
        notes: str = "",
    ) -> int:
        topts = [t.model_dump() for t in recommendation.transfer_options]
        row = RecommendationHistory(
            user_id=user_id,
            squad_snapshot=json.dumps(_squad_to_dict(squad)),
            recommendation=json.dumps(_rec_to_dict(recommendation)),
            captain_id=recommendation.captain,
            transfer_action=recommendation.transfer_action,
            transfer_options_json=json.dumps(topts),
            notes=notes,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row.id

    def get_latest(self, user_id: str) -> MemoryRecordOut | None:
        row = (
            self._db.query(RecommendationHistory)
            .filter(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .first()
        )
        if row is None:
            return None
        return self._row_to_out(row)

    def list_recent(self, user_id: str, limit: int = 10) -> list[MemoryRecordOut]:
        rows = (
            self._db.query(RecommendationHistory)
            .filter(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._row_to_out(r) for r in rows]

    def _row_to_out(self, row: RecommendationHistory) -> MemoryRecordOut:
        return MemoryRecordOut(
            id=row.id,
            user_id=row.user_id,
            created_at=row.created_at.isoformat() + "Z",
            squad_snapshot=row.squad_dict(),
            recommendation=row.recommendation_dict(),
            captain_id=row.captain_id,
            transfer_action=row.transfer_action,
            transfer_options_json=row.transfer_options_list(),
            notes=row.notes or "",
        )
