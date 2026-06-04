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

class ViolationReviewAction(BaseModel):
    action: str = Field(..., description="Action to perform: 'APPROVE' or 'DISMISS'")
    officer_badge: Optional[str] = Field(None, example="UK-POL-7718")
    notes: Optional[str] = Field(None, example="Verified license plate via visual crop.")

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[str]
    action_type: str
    details: str
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SegmentEmissions(BaseModel):
    vehicle_type: str
    emission_standard: str
    transits_count: int
    co2_emitted_kg: float
    pm_emitted_g: float

class EmissionsSummary(BaseModel):
    total_vehicles: int
    total_transits: int
    corridor_distance_km: float
    total_co2_kg: float
    total_pm_g: float
    trees_offset_required: int
    offset_cost_inr: float
    idle_savings_kg: float
    segments: List[SegmentEmissions]

class EmissionsHistoryOut(BaseModel):
    id: int
    calculated_at: datetime
    total_vehicles: int
    total_transits: int
    total_co2_kg: float
    total_pm_g: float
    trees_offset: int
    offset_cost_inr: float
    idle_savings_kg: float
    segment_data: Optional[List[SegmentEmissions]] = None

    class Config:
        from_attributes = True

