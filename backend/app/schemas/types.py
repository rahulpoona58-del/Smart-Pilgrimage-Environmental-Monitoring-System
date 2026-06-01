from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class SystemHealth(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"

class VehicleLogCreate(BaseModel):
    plate_number: str = Field(..., example="UK07TA1234")
    camera_id: str = Field(..., example="CAM-GK-ENTRY")
    location_id: int = Field(..., example=1)
    log_type: str = Field(..., example="ENTRY") # 'ENTRY' or 'EXIT'
    timestamp: datetime
    raw_confidence: float = Field(..., ge=0.0, le=1.0)

class VehicleLogOut(BaseModel):
    id: int
    plate_number: str
    camera_id: str
    location_id: int
    log_type: str
    timestamp: datetime
    raw_confidence: float
    created_at: datetime

    class Config:
        from_attributes = True

class ViolationOut(BaseModel):
    id: int
    location_id: int
    camera_id: str
    plate_number: Optional[str]
    violation_type: str
    severity_level: str
    evidence_image_url: str
    evidence_video_url: Optional[str]
    evidence_hash: Optional[str]
    violation_timestamp: datetime
    status: str
    challan_reference: Optional[str]
    fine_amount_inr: float
    created_at: datetime

    class Config:
        from_attributes = True

class TelemetryCreate(BaseModel):
    location_id: int
    device_id: str
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    aqi: Optional[int] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2: Optional[float] = None
    water_ph: Optional[float] = None
    measured_at: datetime

class TelemetryOut(BaseModel):
    id: int
    location_id: int
    device_id: str
    pm25: Optional[float]
    pm10: Optional[float]
    aqi: Optional[int]
    temperature: Optional[float]
    humidity: Optional[float]
    co2: Optional[float]
    water_ph: Optional[float]
    measured_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
