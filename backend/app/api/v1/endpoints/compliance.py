from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....db.session import get_async_db
from ....core.compliance import ComplianceScoringEngine

router = APIRouter()

@router.get("/vehicle/{plate_number}")
async def get_vehicle_compliance(
    plate_number: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Fetches real-time compliance score and environmental risk ratings for a vehicle.
    Applies penalty calculations over rolling 30-day timelines.
    """
    try:
        score_data = await ComplianceScoringEngine.calculate_vehicle_compliance_score(db, plate_number)
        return score_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring engine evaluation failed: {e}"
        )

@router.get("/location/{location_id}")
async def get_location_compliance(
    location_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves the composite Green Index for a pilgrimage location.
    Integrates 24h moving AQI averages, active waste tracking, and pedestrian congestion counts.
    """
    score_data = await ComplianceScoringEngine.calculate_location_compliance_score(db, location_id)
    if "error" in score_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=score_data["error"]
        )
    return score_data

@router.get("/route")
async def get_route_compliance(
    location_ids: List[int] = Query(..., description="List of location IDs representing the travel route"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Calculates composite path ratings across pilgrimage routes (e.g. Char Dham Yatra trail).
    Averages indices of all active checkpoint nodes.
    """
    try:
        route_data = await ComplianceScoringEngine.calculate_route_compliance_score(db, location_ids)
        return route_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route evaluation failed: {e}"
        )
