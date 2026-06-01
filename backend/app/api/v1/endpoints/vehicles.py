from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from pydantic import BaseModel

from ....db.session import get_async_db
from ....db.models import Vehicle

router = APIRouter()

# Schema for Pydantic validation
class VehicleCreate(BaseModel):
    plate_number: str
    vehicle_type: str
    emission_standard: str = "BS-VI"
    fuel_type: str = "Petrol"
    registered_owner: str
    contact_number: str

class VehicleOut(BaseModel):
    plate_number: str
    vehicle_type: str
    emission_standard: str
    fuel_type: str
    compliance_score: int
    risk_rating: str
    registered_owner: str
    contact_number: str

    class Config:
        from_attributes = True

@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def register_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_async_db)):
    """Registers a new vehicle in the system database."""
    query = select(Vehicle).where(Vehicle.plate_number == payload.plate_number)
    result = await db.execute(query)
    exists = result.scalars().first()
    
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle plate number already registered."
        )

    new_vehicle = Vehicle(
        plate_number=payload.plate_number,
        vehicle_type=payload.vehicle_type,
        emission_standard=payload.emission_standard,
        fuel_type=payload.fuel_type,
        compliance_score=100,
        risk_rating="Low",
        registered_owner=payload.registered_owner,
        contact_number=payload.contact_number
    )
    
    db.add(new_vehicle)
    await db.commit()
    await db.refresh(new_vehicle)
    return new_vehicle

@router.get("/{plate_number}", response_model=VehicleOut)
async def get_vehicle(plate_number: str, db: AsyncSession = Depends(get_async_db)):
    """Fetches a specific vehicle's registry details."""
    query = select(Vehicle).where(Vehicle.plate_number == plate_number)
    result = await db.execute(query)
    vehicle = result.scalars().first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle plate profile not found."
        )
    return vehicle

# ----------------------------------------------------------------------------
# Cross-Camera Re-Identification & Journey Timelines API
# ----------------------------------------------------------------------------
from ....db.models import VehicleLog
from pydantic import Field
from datetime import datetime

class JourneyStop(BaseModel):
    camera_id: str
    location_id: int
    log_type: str
    timestamp: datetime

    class Config:
        from_attributes = True

class VehicleJourneyOut(BaseModel):
    plate_number: str
    vehicle_type: str
    compliance_score: int
    risk_rating: str
    journey_stops: List[JourneyStop]

@router.get("/{plate_number}/journey", response_model=VehicleJourneyOut)
async def get_vehicle_journey_timeline(plate_number: str, db: AsyncSession = Depends(get_async_db)):
    """
    Re-identifies a vehicle across multiple CCTV camera checkpoints,
    generating a chronological movement timeline of its journey.
    """
    # 1. Fetch vehicle metadata
    query_v = select(Vehicle).where(Vehicle.plate_number == plate_number)
    res_v = await db.execute(query_v)
    vehicle = res_v.scalars().first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle profile not found in master registry."
        )

    # 2. Fetch all transit logs chronologically
    query_logs = select(VehicleLog).where(
        VehicleLog.plate_number == plate_number
    ).order_by(VehicleLog.timestamp.asc())
    
    res_logs = await db.execute(query_logs)
    logs = res_logs.scalars().all()

    timeline = [
        JourneyStop(
            camera_id=log.camera_id,
            location_id=log.location_id,
            log_type=log.log_type,
            timestamp=log.timestamp
        )
        for log in logs
    ]

    return VehicleJourneyOut(
        plate_number=vehicle.plate_number,
        vehicle_type=vehicle.vehicle_type,
        compliance_score=vehicle.compliance_score,
        risk_rating=vehicle.risk_rating,
        journey_stops=timeline
    )
