from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_memory_repo
from app.repositories.memory_repository import SQLiteMemoryRepository
from app.schemas import MemoryRecordOut

router = APIRouter(prefix="/api", tags=["memory"])


@router.get("/memory/{user_id}", response_model=MemoryRecordOut | None)
def get_latest_memory(
    user_id: str,
    repo: SQLiteMemoryRepository = Depends(get_memory_repo),
) -> MemoryRecordOut | None:
    return repo.get_latest(user_id)


@router.get("/memory/{user_id}/sessions", response_model=list[MemoryRecordOut])
def list_sessions(
    user_id: str,
    limit: int = 10,
    repo: SQLiteMemoryRepository = Depends(get_memory_repo),
) -> list[MemoryRecordOut]:
    return repo.list_recent(user_id, limit=min(limit, 50))
