from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List

from ....db.session import get_async_db
from ....db.models import Camera, Location

router = APIRouter()

class CameraCreate(BaseModel):
    id: str
    location_id: int
    model_name: str
    rtsp_url: str
    latitude: float
    longitude: float
    direction_angle: float = 0.0

class CameraOut(BaseModel):
    id: str
    location_id: int
    model_name: str
    rtsp_url: str
    direction_angle: float
    is_active: bool

    class Config:
        from_attributes = True

@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
async def register_camera(payload: CameraCreate, db: AsyncSession = Depends(get_async_db)):
    """Registers a new physical camera node geofenced to a location."""
    # Ensure camera ID doesn't already exist
    query = select(Camera).where(Camera.id == payload.id)
    result = await db.execute(query)
    exists = result.scalars().first()
    
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Camera ID already registered."
        )

    # Convert coordinates coordinates to PostGIS Point format
    spatial_point = f"SRID=4326;POINT({payload.longitude} {payload.latitude})"

    new_camera = Camera(
        id=payload.id,
        location_id=payload.location_id,
        model_name=payload.model_name,
        rtsp_url=payload.rtsp_url,
        georeference_coords=spatial_point,
        direction_angle=payload.direction_angle,
        is_active=True
    )

    db.add(new_camera)
    await db.commit()
    await db.refresh(new_camera)
    return new_camera

@router.get("", response_model=List[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_async_db)):
    """Retrieves all active camera nodes."""
    query = select(Camera)
    result = await db.execute(query)
    cameras = result.scalars().all()
    return cameras
