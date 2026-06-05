import os
from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/buffer.db")
is_sqlite = "sqlite" in DATABASE_URL

if is_sqlite:
    # Relaxed SQLite fallback: use standard types, avoiding PostGIS and PostgreSQL-specific DDL constraints
    Geometry = lambda *args, **kwargs: String(512)
    ARRAY = lambda *args, **kwargs: String(256)
    UUID = lambda *args, **kwargs: String(36)
else:
    from geoalchemy2 import Geometry
    from sqlalchemy.dialects.postgresql import UUID, ARRAY

from .session import Base

class Authority(Base):
    __tablename__ = "authorities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    department = Column(String(100), nullable=False)
    state = Column(String(50), default="Uttarakhand")
    contact_email = Column(String(100), nullable=False)
    api_endpoint = Column(String(256))
    api_key_hash = Column(String(128))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="authority")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authority_id = Column(Integer, ForeignKey("authorities.id", ondelete="SET NULL"))
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(30), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(15))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    authority = relationship("Authority", back_populates="users")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    district = Column(String(50), nullable=False)
    altitude_meters = Column(Integer)
    
    # postgis geospatial polygon and points representation
    geom = Column(Geometry("POLYGON", srid=4326), nullable=False)
    center_point = Column(Geometry("POINT", srid=4326), nullable=False)
    
    pedestrian_capacity_limit = Column(Integer, nullable=False)
    vehicle_capacity_limit = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cameras = relationship("Camera", back_populates="location")
    telemetry = relationship("SensorData", back_populates="location")
    violations = relationship("Violation", back_populates="location")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(50), primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"), index=True)
    model_name = Column(String(100))
    rtsp_url = Column(String(512), nullable=False)
    georeference_coords = Column(Geometry("POINT", srid=4326), nullable=False)
    direction_angle = Column(Numeric(5, 2))
    is_active = Column(Boolean, default=True)
    ai_features_enabled = Column(ARRAY(String(50)), default="VEHICLE_TRACK,ANPR" if is_sqlite else ["VEHICLE_TRACK", "ANPR"])
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", back_populates="cameras")
    violations = relationship("Violation", back_populates="camera")

class Vehicle(Base):
    __tablename__ = "vehicles"

    plate_number = Column(String(20), primary_key=True)
    vehicle_type = Column(String(30), nullable=False)
    emission_standard = Column(String(15), default="BS-VI")
    fuel_type = Column(String(15), nullable=False)
    compliance_score = Column(Integer, default=100)
    registered_owner = Column(String(100), nullable=False)
    contact_number = Column(String(15), nullable=False)
    chassis_number = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    violations = relationship("Violation", back_populates="vehicle")

    @property
    def risk_rating(self) -> str:
        score = self.compliance_score if self.compliance_score is not None else 100
        if score > 75:
            return "Low"
        elif score > 45:
            return "Medium"
        else:
            return "High"

    @risk_rating.setter
    def risk_rating(self, value: str):
        pass # Ignore setting directly since it is dynamically calculated from compliance_score

class VehicleLog(Base):
    __tablename__ = "vehicle_logs"

    id = Column(Integer, primary_key=True)
    plate_number = Column(String(20), ForeignKey("vehicles.plate_number", ondelete="CASCADE"), index=True)
    camera_id = Column(String(50), ForeignKey("cameras.id", ondelete="RESTRICT"))
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"))
    log_type = Column(String(10), nullable=False) # 'ENTRY', 'EXIT'
    timestamp = Column(DateTime(timezone=True), nullable=False, primary_key=not is_sqlite) # Composite key for range partitions in Postgres
    raw_confidence = Column(Numeric(3, 2))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"))
    device_id = Column(String(50), nullable=False)
    pm25 = Column(Numeric(6, 2))
    pm10 = Column(Numeric(6, 2))
    aqi = Column(Integer)
    temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    co2 = Column(Numeric(7, 2))
    water_ph = Column(Numeric(4, 2))
    measured_at = Column(DateTime(timezone=True), nullable=False, primary_key=not is_sqlite) # Range partition key in Postgres
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", back_populates="telemetry")

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="RESTRICT"))
    camera_id = Column(String(50), ForeignKey("cameras.id", ondelete="RESTRICT"))
    plate_number = Column(String(20), ForeignKey("vehicles.plate_number", ondelete="SET NULL"), nullable=True)
    drone_feed_id = Column(UUID(as_uuid=True), nullable=True)
    violation_type = Column(String(50), nullable=False) # 'Littering', 'Illegal_Parking', 'Restricted_Zone_Entry', 'Overcrowding'
    severity_level = Column(String(10), default="Medium")
    evidence_image_url = Column(String(512), nullable=False)
    evidence_video_url = Column(String(512))
    evidence_hash = Column(String(64), unique=True, nullable=True) # Cryptographic evidence seal for legal admissibility
    violation_coordinates = Column(Geometry("POINT", srid=4326), nullable=False)
    violation_timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), default="PENDING") # 'PENDING', 'APPROVED', 'DISMISSED', 'CHALLAN_ISSUED'
    challan_reference = Column(String(50), unique=True)
    fine_amount_inr = Column(Numeric(8, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", back_populates="violations")
    camera = relationship("Camera", back_populates="violations")
    vehicle = relationship("Vehicle", back_populates="violations")

class EnvironmentalScore(Base):
    __tablename__ = "environmental_scores"

    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=True)
    vehicle_plate = Column(String(20), ForeignKey("vehicles.plate_number", ondelete="CASCADE"), nullable=True)
    measured_date = Column(DateTime, nullable=False)
    air_quality_score = Column(Integer)
    waste_compliance_score = Column(Integer)
    noise_compliance_score = Column(Integer)
    composite_eco_index = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(50), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), primary_key=not is_sqlite)

class EmissionsHistory(Base):
    __tablename__ = "emissions_history"

    id = Column(Integer, primary_key=True)
    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total_vehicles = Column(Integer, nullable=False)
    total_transits = Column(Integer, nullable=False)
    total_co2_kg = Column(Numeric(12, 2), nullable=False)
    total_pm_g = Column(Numeric(12, 2), nullable=False)
    trees_offset = Column(Integer, nullable=False)
    offset_cost_inr = Column(Numeric(12, 2), nullable=False)
    idle_savings_kg = Column(Numeric(12, 2), nullable=False)
    segment_data = Column(JSON, nullable=True) # Mapped details for segment breakdowns

class ModelTrainingMetrics(Base):
    __tablename__ = "model_training_metrics"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(50), nullable=False) # 'pollution', 'traffic', 'crowd', 'litter'
    trained_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    mae = Column(Numeric(8, 4), nullable=False)
    rmse = Column(Numeric(8, 4), nullable=False)
    r2 = Column(Numeric(8, 4), nullable=False)
    training_samples = Column(Integer, nullable=False)

class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True)
    target_type = Column(String(50), nullable=False) # 'pollution', 'traffic', 'crowd', 'litter'
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    predicted_value = Column(Numeric(12, 4), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    predicted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    target_time = Column(DateTime(timezone=True), nullable=False)
    features_used = Column(JSON, nullable=True)


