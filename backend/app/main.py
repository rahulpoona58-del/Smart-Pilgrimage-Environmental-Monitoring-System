from fastapi import FastAPI, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from typing import Optional

from .db.session import get_async_db
from .db.models import VehicleLog, SensorData, Vehicle
from .schemas.types import SystemHealth, VehicleLogCreate, VehicleLogOut, TelemetryCreate, TelemetryOut
from .api.v1.endpoints import violations, compliance, vehicles, cameras, reports
from .core.logging_config import setup_system_logging

# Start logging handlers
setup_system_logging()

app = FastAPI(
    title="Smart Pilgrimage Environmental Monitoring System API",
    description="Core backend orchestrator serving spatial databases, analytics, and RTO interfaces.",
    version="1.0.0"
)

# Enable CORS middleware to support client dashboards running on different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to internal domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: http://localhost:8001 /static/;"
    return response

# Ensure required directories exist and mount static route to serve violation image evidence
import os
os.makedirs("static/evidence", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Modular Routers
app.include_router(violations.router, prefix="/api/v1/violations", tags=["violations"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])
app.include_router(vehicles.router, prefix="/api/v1/vehicles", tags=["vehicles"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["cameras"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])

@app.on_event("startup")
async def startup_event():
    """Automatically initialize database tables on startup if they don't exist and seed default location and camera nodes."""
    from .db.session import engine, Base, async_session_maker
    from .db.models import Location, Camera
    from sqlalchemy.future import select
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # 1. Seed Locations if absent
        res_loc = await session.execute(select(Location).limit(1))
        if not res_loc.scalars().first():
            print("[Startup Seeder] Seeding default pilgrimage checkpoints...")
            loc1 = Location(
                id=1,
                name="Kedarnath Base Camp (Gaurikund)",
                district="Rudraprayag",
                altitude_meters=1982,
                geom="SRID=4326;POLYGON((78.9950 30.6400, 79.0150 30.6400, 79.0150 30.6600, 78.9950 30.6600, 78.9950 30.6400))",
                center_point="SRID=4326;POINT(79.0050 30.6500)",
                pedestrian_capacity_limit=5000,
                vehicle_capacity_limit=1000
            )
            loc2 = Location(
                id=2,
                name="Badrinath Entrance Checkpoint",
                district="Chamoli",
                altitude_meters=3133,
                geom="SRID=4326;POLYGON((79.4800 30.7300, 79.5000 30.7300, 79.5000 30.7500, 79.4800 30.7500, 79.4800 30.7300))",
                center_point="SRID=4326;POINT(79.4900 30.7400)",
                pedestrian_capacity_limit=8000,
                vehicle_capacity_limit=2000
            )
            session.add_all([loc1, loc2])

        # 2. Seed Cameras if absent
        res_cam = await session.execute(select(Camera).limit(1))
        if not res_cam.scalars().first():
            print("[Startup Seeder] Seeding default CCTV camera nodes...")
            cam1 = Camera(
                id="CAM-GK-ENTRY",
                location_id=1,
                model_name="Hikvision Outdoor PTZ 4K",
                rtsp_url="rtsp://mock-video-stream:8554/gk-entry",
                georeference_coords="SRID=4326;POINT(79.0050 30.6500)",
                direction_angle=0.0,
                is_active=True
            )
            cam2 = Camera(
                id="CAM-GK-RIVER-04",
                location_id=1,
                model_name="Hikvision Outdoor PTZ 4K",
                rtsp_url="rtsp://mock-video-stream:8554/gk-river",
                georeference_coords="SRID=4326;POINT(79.0058 30.6508)",
                direction_angle=90.0,
                is_active=True
            )
            cam3 = Camera(
                id="CAM-GK-TEST-99",
                location_id=1,
                model_name="Hikvision Outdoor PTZ 4K",
                rtsp_url="rtsp://internal-ip-mock/live",
                georeference_coords="SRID=4326;POINT(79.0052 30.6502)",
                direction_angle=0.0,
                is_active=True
            )
            session.add_all([cam1, cam2, cam3])

        await session.commit()

@app.get("/health", response_model=SystemHealth)
async def system_health_check():
    """Service health validation node."""
    return SystemHealth(
        status="OK",
        timestamp=datetime.now(timezone.utc)
    )

# ----------------------------------------------------------------------------
# Inline Vehicle Logs Router (Entry/Exit Tracking)
# ----------------------------------------------------------------------------
@app.post("/api/v1/logs/vehicle", response_model=VehicleLogOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle_transit_log(payload: VehicleLogCreate, db: AsyncSession = Depends(get_async_db)):
    """Logs vehicle transit points and validates against RTO database registries."""
    # Ensure vehicle registration exists, if not initialize profile
    query = select(Vehicle).where(Vehicle.plate_number == payload.plate_number)
    result = await db.execute(query)
    vehicle = result.scalars().first()

    if not vehicle:
        # Create virtual vehicle registry record matching plate
        vehicle = Vehicle(
            plate_number=payload.plate_number,
            vehicle_type="Car",
            emission_standard="BS-VI",
            fuel_type="Petrol",
            compliance_score=100,
            registered_owner="Himalayan Visitor",
            contact_number="+910000000000"
        )
        db.add(vehicle)

    new_log = VehicleLog(
        plate_number=payload.plate_number,
        camera_id=payload.camera_id,
        location_id=payload.location_id,
        log_type=payload.log_type,
        timestamp=payload.timestamp,
        raw_confidence=payload.raw_confidence
    )

    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)

    return new_log

# ----------------------------------------------------------------------------
# Inline IoT Telemetry Router (Air, Water, Climate Sensors)
# ----------------------------------------------------------------------------
@app.post("/api/v1/telemetry", response_model=TelemetryOut, status_code=status.HTTP_201_CREATED)
async def log_iot_sensor_telemetry(payload: TelemetryCreate, db: AsyncSession = Depends(get_async_db)):
    """Receives high-frequency environmental readings from IoT hubs."""
    new_telemetry = SensorData(
        location_id=payload.location_id,
        device_id=payload.device_id,
        pm25=payload.pm25,
        pm10=payload.pm10,
        aqi=payload.aqi,
        temperature=payload.temperature,
        humidity=payload.humidity,
        co2=payload.co2,
        water_ph=payload.water_ph,
        measured_at=payload.measured_at
    )

    db.add(new_telemetry)
    await db.commit()
    await db.refresh(new_telemetry)

    return new_telemetry

@app.get("/api/v1/telemetry", response_model=list[TelemetryOut])
async def get_latest_telemetries(location_id: Optional[int] = None, limit: int = 20, db: AsyncSession = Depends(get_async_db)):
    """Fetches sensor logs sorted chronologically."""
    query = select(SensorData)
    if location_id:
        query = query.where(SensorData.location_id == location_id)
    query = query.order_by(SensorData.measured_at.desc()).limit(limit)
    
    result = await db.execute(query)
    records = result.scalars().all()
    return records
