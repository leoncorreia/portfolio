from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_team_import_service
from app.schemas import TeamImportRequest, TeamImportResponse
from app.services.team_import_service import TeamImportService

router = APIRouter(prefix="/api", tags=["import"])


@router.post("/import-team", response_model=TeamImportResponse)
async def import_team(
    body: TeamImportRequest,
    svc: TeamImportService = Depends(get_team_import_service),
) -> TeamImportResponse:
    try:
        return await svc.import_team(
            body.team_id,
            body.free_transfers,
            body.bank,
            body.risk_profile,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
