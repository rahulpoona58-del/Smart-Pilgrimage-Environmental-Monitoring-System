# backend/app/api/v1/endpoints/disaster.py
# API endpoints for Disaster Monitoring hazard evaluation and alerts management.

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import cv2
import numpy as np
from typing import List, Optional

from ....db.session import get_async_db
from ....core.disaster import DisasterMonitoringService
from ....schemas.types import DisasterAlertOut, DisasterStatus

router = APIRouter()

@router.get("/alerts", response_model=List[DisasterAlertOut])
async def get_active_disaster_alerts(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieves all active regional disaster alerts (landslides, flooding, rockfalls).
    """
    try:
        alerts = await DisasterMonitoringService.get_active_alerts(db)
        return alerts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch active alerts: {e}"
        )

@router.post("/alerts/{alert_id}/resolve", response_model=DisasterAlertOut)
async def resolve_disaster_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Flags an environmental hazard alert as resolved.
    """
    try:
        alert = await DisasterMonitoringService.resolve_alert(db, alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disaster alert record not found."
            )
        return alert
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {e}"
        )

@router.get("/status/{location_id}", response_model=DisasterStatus)
async def get_location_disaster_status(
    location_id: int,
    camera_id: Optional[str] = "CAM-GK-ENTRY",
    db: AsyncSession = Depends(get_async_db)
):
    """
    Evaluates current risk scores and composite hazard indexes for a location using telemetry data.
    Fails over to a safe index calculation when video feeds are offline.
    """
    try:
        # Create empty mock frames for passive check without direct video stream upload
        dummy_prev = np.zeros((100, 100), dtype=np.uint8)
        dummy_curr = np.zeros((100, 100), dtype=np.uint8)
        
        status_res = await DisasterMonitoringService.update_disaster_hazards(
            db=db,
            location_id=location_id,
            camera_id=camera_id,
            prev_frame=dummy_prev,
            curr_frame=dummy_curr
        )
        return status_res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch disaster status: {e}"
        )

@router.post("/evaluate/{location_id}", response_model=DisasterStatus)
async def evaluate_disaster_frames(
    location_id: int,
    camera_id: str,
    prev_frame: UploadFile = File(...),
    curr_frame: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Accepts two sequential camera frames via multipart upload, calculates real-time optical flow,
    and returns a composite landslide/flooding index evaluation.
    """
    try:
        # Read frames from upload files
        prev_bytes = await prev_frame.read()
        curr_bytes = await curr_frame.read()
        
        prev_arr = np.frombuffer(prev_bytes, np.uint8)
        curr_arr = np.frombuffer(curr_bytes, np.uint8)
        
        img_prev = cv2.imdecode(prev_arr, cv2.IMREAD_COLOR)
        img_curr = cv2.imdecode(curr_arr, cv2.IMREAD_COLOR)
        
        if img_prev is None or img_curr is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format in upload payload."
            )
            
        status_res = await DisasterMonitoringService.update_disaster_hazards(
            db=db,
            location_id=location_id,
            camera_id=camera_id,
            prev_frame=img_prev,
            curr_frame=img_curr
        )
        return status_res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate uploaded frames: {e}"
        )
