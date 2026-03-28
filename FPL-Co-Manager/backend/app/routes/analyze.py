from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_memory_service
from app.schemas import AnalyzeTeamRequest, AnalyzeTeamResponse
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeTeamResponse)
async def analyze(
    body: AnalyzeTeamRequest,
    svc: MemoryService = Depends(get_memory_service),
) -> AnalyzeTeamResponse:
    if not body.squad.players:
        raise HTTPException(status_code=400, detail="Squad has no players.")
    return await svc.analyze_with_memory(body.user_id, body.squad, body.use_memory)
