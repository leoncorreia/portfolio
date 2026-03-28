from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_compare_service
from app.schemas import CompareSummary, CompareTeamRequest
from app.services.compare_service import CompareService

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare-last", response_model=CompareSummary)
async def compare_last(
    body: CompareTeamRequest,
    svc: CompareService = Depends(get_compare_service),
) -> CompareSummary:
    if not body.squad.players:
        raise HTTPException(status_code=400, detail="Squad has no players.")
    return await svc.compare_last_vs_current(body.user_id, body.squad)
