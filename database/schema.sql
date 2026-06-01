-- ============================================================================
-- SMART PILGRIMAGE ENVIRONMENTAL MONITORING & COMPLIANCE SYSTEM (SPEMS)
-- Enterprise-Grade Database Schema (PostgreSQL 15+ & PostGIS Extension)
-- Optimized for: 10,000+ CCTV Nodes, 1M+ Vehicles/Month, high-frequency IoT
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Extensions
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- Cleanup (Reverse dependency order)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS environmental_scores CASCADE;
DROP TABLE IF EXISTS violations CASCADE;
DROP TABLE IF EXISTS drone_feeds CASCADE;
DROP TABLE IF EXISTS sensor_data CASCADE;
DROP TABLE IF EXISTS vehicle_logs CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS cameras CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS authorities CASCADE;

-- ----------------------------------------------------------------------------
-- 1. AUTHORITIES TABLE (Government bodies & departments)
-- ----------------------------------------------------------------------------
CREATE TABLE authorities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL, -- e.g., 'Transport', 'Pollution Control', 'Forestry'
    state VARCHAR(50) DEFAULT 'Uttarakhand',
    contact_email VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(256), -- Webhook URL for external Gov integration
    api_key_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. USERS TABLE (System administrators, inspectors, and authority officials)
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    authority_id INT REFERENCES authorities(id) ON DELETE SET NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('SUPER_ADMIN', 'GOVT_OFFICIAL', 'EDGE_OPERATOR', 'AUDITOR')),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone_number VARCHAR(15),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_authority ON users(authority_id);
CREATE INDEX idx_users_username ON users(username);

-- ----------------------------------------------------------------------------
-- 3. LOCATIONS TABLE (Shrines, valleys, base camps, roads)
-- ----------------------------------------------------------------------------
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    district VARCHAR(50) NOT NULL, -- e.g., 'Rudraprayag', 'Chamoli', 'Uttarkashi'
    altitude_meters INT CHECK (altitude_meters > 0),
    geom GEOMETRY(Polygon, 4326) NOT NULL, -- Geo-fenced perimeter of the entire zone
    center_point GEOMETRY(Point, 4326) NOT NULL, -- Centroid of the region
    pedestrian_capacity_limit INT NOT NULL CHECK (pedestrian_capacity_limit > 0),
    vehicle_capacity_limit INT NOT NULL CHECK (vehicle_capacity_limit > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_locations_geom ON locations USING gist(geom);
CREATE INDEX idx_locations_center ON locations USING gist(center_point);

-- ----------------------------------------------------------------------------
-- 4. CAMERAS TABLE (10,000+ CCTV Camera Nodes)
-- ----------------------------------------------------------------------------
CREATE TABLE cameras (
    id VARCHAR(50) PRIMARY KEY, -- e.g., 'CAM-GK-ENTRY-01'
    location_id INT REFERENCES locations(id) ON DELETE RESTRICT,
    model_name VARCHAR(100),
    rtsp_url VARCHAR(512) NOT NULL,
    georeference_coords GEOMETRY(Point, 4326) NOT NULL, -- Physical camera placement
    direction_angle NUMERIC(5,2), -- Camera view direction (0-360 degrees)
    is_active BOOLEAN DEFAULT TRUE,
    ai_features_enabled VARCHAR(50)[] DEFAULT ARRAY['VEHICLE_TRACK', 'ANPR'], -- Dynamic CV stack features
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cameras_location ON cameras(location_id);
CREATE INDEX idx_cameras_coords ON cameras USING gist(georeference_coords);

-- ----------------------------------------------------------------------------
-- 5. VEHICLES TABLE (Master Registry for Emission & Green Scores)
-- ----------------------------------------------------------------------------
CREATE TABLE vehicles (
    plate_number VARCHAR(20) PRIMARY KEY,
    vehicle_type VARCHAR(30) NOT NULL CHECK (vehicle_type IN ('Car', 'SUV', 'Truck', 'Bus', 'Two-Wheeler', 'Commercial-Van')),
    emission_standard VARCHAR(15) NOT NULL DEFAULT 'BS-VI', -- 'BS-IV', 'BS-V', 'BS-VI', 'EV', 'CNG'
    fuel_type VARCHAR(15) NOT NULL CHECK (fuel_type IN ('Petrol', 'Diesel', 'CNG', 'Electric', 'Hybrid')),
    compliance_score INT DEFAULT 100 CHECK (compliance_score BETWEEN 0 AND 100),
    registered_owner VARCHAR(100) NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    chassis_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_compliance ON vehicles(compliance_score);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type);

-- ----------------------------------------------------------------------------
-- 6. VEHICLE INGRESS/EGRESS LOGS (High transaction throughput table)
-- ----------------------------------------------------------------------------
CREATE TABLE vehicle_logs (
    id BIGSERIAL,
    plate_number VARCHAR(20) REFERENCES vehicles(plate_number) ON DELETE CASCADE,
    camera_id VARCHAR(50) REFERENCES cameras(id) ON DELETE RESTRICT,
    location_id INT REFERENCES locations(id) ON DELETE RESTRICT,
    log_type VARCHAR(10) NOT NULL CHECK (log_type IN ('ENTRY', 'EXIT')),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    raw_confidence NUMERIC(3,2) CHECK (raw_confidence BETWEEN 0.0 AND 1.0), -- ANPR OCR Confidence
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, timestamp) -- Combined primary key required for partitioning if applied later
);

CREATE INDEX idx_vehicle_logs_timestamp ON vehicle_logs(timestamp DESC);
CREATE INDEX idx_vehicle_logs_plate_time ON vehicle_logs(plate_number, timestamp DESC);
CREATE INDEX idx_vehicle_logs_location ON vehicle_logs(location_id, timestamp DESC);

-- ----------------------------------------------------------------------------
-- 7. SENSOR DATA TABLE (IoT air, weather & water telemetries - RANGE PARTITIONED)
-- ----------------------------------------------------------------------------
CREATE TABLE sensor_data (
    id BIGSERIAL,
    location_id INT REFERENCES locations(id) ON DELETE CASCADE,
    device_id VARCHAR(50) NOT NULL,
    pm25 NUMERIC(6,2),
    pm10 NUMERIC(6,2),
    aqi INT,
    temperature NUMERIC(5,2),
    humidity NUMERIC(5,2),
    co2 NUMERIC(7,2),
    water_ph NUMERIC(4,2), -- water pollution index
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, measured_at)
) PARTITION BY RANGE (measured_at);

-- Partition Tables for Time-Series Optimization (Daily/Monthly partitions)
-- Creating initial partition ranges for local validation
CREATE TABLE sensor_data_y2026m06 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

CREATE TABLE sensor_data_y2026m07 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-08-01 00:00:00+00');

CREATE TABLE sensor_data_default PARTITION OF sensor_data DEFAULT;

-- Time-Series Indices (Will be created automatically on partitions)
CREATE INDEX idx_sensor_data_time ON sensor_data(measured_at DESC);
CREATE INDEX idx_sensor_data_loc_time ON sensor_data(location_id, measured_at DESC);

-- ----------------------------------------------------------------------------
-- 8. DRONE FEEDS TABLE (Logs of UAV patrol routes)
-- ----------------------------------------------------------------------------
CREATE TABLE drone_feeds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id INT REFERENCES locations(id) ON DELETE CASCADE,
    drone_uav_id VARCHAR(50) NOT NULL,
    pilot_license_no VARCHAR(50),
    stream_rtmp_url VARCHAR(512),
    flight_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    flight_end_time TIMESTAMP WITH TIME ZONE,
    average_altitude_meters NUMERIC(6,2),
    gps_flight_path GEOMETRY(LineString, 4326), -- LineString representing coordinates traveled
    battery_level_percent INT CHECK (battery_level_percent BETWEEN 0 AND 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_drone_feeds_location ON drone_feeds(location_id);
CREATE INDEX idx_drone_feeds_flight_time ON drone_feeds(flight_start_time DESC);
CREATE INDEX idx_drone_feeds_path ON drone_feeds USING gist(gps_flight_path);

-- ----------------------------------------------------------------------------
-- 9. ENVIRONMENTAL VIOLATION REGISTRY (Legal evidence ledger)
-- ----------------------------------------------------------------------------
CREATE TABLE violations (
    id BIGSERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id) ON DELETE RESTRICT,
    camera_id VARCHAR(50) REFERENCES cameras(id) ON DELETE RESTRICT,
    plate_number VARCHAR(20) REFERENCES vehicles(plate_number) ON DELETE SET NULL, -- Null if pedestrian
    drone_feed_id UUID REFERENCES drone_feeds(id) ON DELETE SET NULL, -- Linked if flagged by drone
    violation_type VARCHAR(50) NOT NULL CHECK (violation_type IN ('Littering', 'Illegal_Parking', 'Restricted_Zone_Entry', 'Overcrowding', 'River_Pollution')),
    severity_level VARCHAR(10) NOT NULL DEFAULT 'Medium' CHECK (severity_level IN ('Low', 'Medium', 'High')),
    evidence_image_url VARCHAR(512) NOT NULL,
    evidence_video_url VARCHAR(512),
    evidence_hash VARCHAR(64) UNIQUE, -- Cryptographic evidence seal for legal admissibility
    violation_coordinates GEOMETRY(Point, 4326) NOT NULL, -- Spatial geo of infraction
    violation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'DISMISSED', 'CHALLAN_ISSUED', 'FINES_PAID')),
    challan_reference VARCHAR(50) UNIQUE, -- NIC/RTO generated E-challan ID
    fine_amount_inr NUMERIC(8,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_violations_time ON violations(violation_timestamp DESC);
CREATE INDEX idx_violations_loc_time ON violations(location_id, violation_timestamp DESC);
CREATE INDEX idx_violations_coords ON violations USING gist(violation_coordinates);
CREATE INDEX idx_violations_plate ON violations(plate_number) WHERE plate_number IS NOT NULL;
CREATE INDEX idx_violations_status ON violations(status);

-- ----------------------------------------------------------------------------
-- 10. ENVIRONMENTAL SCORES TABLE (Temporal metrics tracking green ratings)
-- ----------------------------------------------------------------------------
CREATE TABLE environmental_scores (
    id BIGSERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id) ON DELETE CASCADE,
    vehicle_plate VARCHAR(20) REFERENCES vehicles(plate_number) ON DELETE CASCADE, -- Can be NULL if score belongs to location
    measured_date DATE NOT NULL,
    air_quality_score INT CHECK (air_quality_score BETWEEN 0 AND 100),
    waste_compliance_score INT CHECK (waste_compliance_score BETWEEN 0 AND 100),
    noise_compliance_score INT CHECK (noise_compliance_score BETWEEN 0 AND 100),
    composite_eco_index INT CHECK (composite_eco_index BETWEEN 0 AND 100), -- Aggregated final compliance score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_score_entity_exists CHECK (
        (location_id IS NOT NULL AND vehicle_plate IS NULL) OR 
        (location_id IS NULL AND vehicle_plate IS NOT NULL)
    ),
    UNIQUE (location_id, vehicle_plate, measured_date)
);

CREATE INDEX idx_env_scores_date ON environmental_scores(measured_date DESC);
CREATE INDEX idx_env_scores_composite ON environmental_scores(composite_eco_index);

-- ----------------------------------------------------------------------------
-- 11. AUDIT LOGS TABLE (Security trail - RANGE PARTITIONED BY TIME)
-- ----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id BIGSERIAL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- e.g., 'LOGIN', 'APPROVE_VIOLATION', 'EDIT_CAMERA', 'EXPORT_DATA'
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Partition Tables for Security Audit
CREATE TABLE audit_logs_y2026m06 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

CREATE TABLE audit_logs_y2026m07 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-08-01 00:00:00+00');

CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT;

CREATE INDEX idx_audit_logs_time ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);

-- ----------------------------------------------------------------------------
-- Common Triggers & Functions
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_authorities BEFORE UPDATE ON authorities FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_locations BEFORE UPDATE ON locations FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_cameras BEFORE UPDATE ON cameras FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_vehicles BEFORE UPDATE ON vehicles FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_update_violations BEFORE UPDATE ON violations FOR EACH ROW EXECUTE FUNCTION update_timestamp();
