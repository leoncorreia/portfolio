"""
Memory / history repository interface.

SQLite implementation lives in memory_repository.py.
TODO: REPLACE_WITH_REAL_HYDRA_MEMORY — implement this interface against HydraDB or Postgres
using HYDRA_DATABASE_URL when migrating off SQLite.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import MemoryRecordOut, Recommendation, Squad


class MemoryRepository(ABC):
    @abstractmethod
    def save_recommendation(
        self,
        user_id: str,
        squad: Squad,
        recommendation: Recommendation,
        notes: str = "",
    ) -> int:
        pass

    @abstractmethod
    def get_latest(self, user_id: str) -> MemoryRecordOut | None:
        pass

    @abstractmethod
    def list_recent(self, user_id: str, limit: int = 10) -> list[MemoryRecordOut]:
        pass
