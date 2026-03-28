"""SQLAlchemy ORM models for persisted recommendation history."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    squad_snapshot: Mapped[str] = mapped_column(Text)  # JSON
    recommendation: Mapped[str] = mapped_column(Text)  # JSON
    captain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transfer_action: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transfer_options_json: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str] = mapped_column(Text, default="")

    def squad_dict(self) -> dict[str, Any]:
        return json.loads(self.squad_snapshot)

    def recommendation_dict(self) -> dict[str, Any]:
        return json.loads(self.recommendation)

    def transfer_options_list(self) -> list[dict[str, Any]]:
        return json.loads(self.transfer_options_json or "[]")
