-- Seed Initial Locations (Kedarnath, Badrinath, Gangotri)
-- Using actual approximate coordinates of Uttarakhand shrines, represented as spatial geofences

INSERT INTO locations (name, district, altitude_meters, geom, center_point, threshold_capacity, current_occupancy)
VALUES (
    'Kedarnath Base Camp (Gaurikund)', 
    'Rudraprayag', 
    1982, 
    ST_GeomFromText('POLYGON((78.9950 30.6400, 79.0150 30.6400, 79.0150 30.6600, 78.9950 30.6600, 78.9950 30.6400))', 4326),
    ST_GeomFromText('POINT(79.0050 30.6500)', 4326),
    5000,
    1450
) ON CONFLICT (name) DO NOTHING;

INSERT INTO locations (name, district, altitude_meters, geom, center_point, threshold_capacity, current_occupancy)
VALUES (
    'Badrinath Entrance Checkpoint', 
    'Chamoli', 
    3133, 
    ST_GeomFromText('POLYGON((79.4800 30.7300, 79.5000 30.7300, 79.5000 30.7500, 79.4800 30.7500, 79.4800 30.7300))', 4326),
    ST_GeomFromText('POINT(79.4900 30.7400)', 4326),
    8000,
    3120
) ON CONFLICT (name) DO NOTHING;

INSERT INTO locations (name, district, altitude_meters, geom, center_point, threshold_capacity, current_occupancy)
VALUES (
    'Gangotri National Park Entrance', 
    'Uttarkashi', 
    3415, 
    ST_GeomFromText('POLYGON((78.9300 30.9800, 78.9500 30.9800, 78.9500 31.0000, 78.9300 31.0000, 78.9300 30.9800))', 4326),
    ST_GeomFromText('POINT(78.9400 30.9900)', 4326),
    3000,
    890
) ON CONFLICT (name) DO NOTHING;

-- Seed Vehicles (Registering standard tourist cabs and utility trucks)
INSERT INTO vehicles (plate_number, vehicle_type, emission_standard, compliance_score, risk_rating, registered_owner, contact_number)
VALUES
    ('UK07TA1234', 'Car', 'BS-VI', 95, 'Low', 'Ramesh Singh Negi', '+919876543210'),
    ('DL1CA5678', 'SUV', 'BS-VI', 80, 'Low', 'Aditya Sharma', '+919988776655'),
    ('HR26CT9999', 'Bus', 'BS-IV', 45, 'High', 'Himalayan Tours Ltd', '+919000111222'),
    ('MH12DE4321', 'Truck', 'BS-V', 72, 'Medium', 'Uttarakhand Logistical Services', '+918888877777'),
    ('UK13G0099', 'Two-Wheeler', 'BS-VI', 100, 'Low', 'Sunita Bisht', '+917766554433')
ON CONFLICT (plate_number) DO NOTHING;

-- Seed Vehicle Ingress Logs (Entries and Exits)
INSERT INTO vehicle_logs (plate_number, location_id, log_type, timestamp, camera_id)
VALUES
    ('UK07TA1234', 1, 'ENTRY', NOW() - INTERVAL '4 hours', 'CAM-GK-01'),
    ('DL1CA5678', 2, 'ENTRY', NOW() - INTERVAL '3 hours', 'CAM-BD-02'),
    ('HR26CT9999', 1, 'ENTRY', NOW() - INTERVAL '2 hours', 'CAM-GK-02'),
    ('UK07TA1234', 1, 'EXIT', NOW() - INTERVAL '30 minutes', 'CAM-GK-03')
ON CONFLICT DO NOTHING;

-- Seed Violations (Pre-loaded evidence of environmental rule breaks)
INSERT INTO violations (location_id, plate_number, violation_type, severity_level, evidence_image_url, violation_coordinates, violation_timestamp, status)
VALUES
    (
        1, 
        'HR26CT9999', 
        'Illegal_Parking', 
        'High', 
        '/evidence/violations/hr26ct9999_parking.jpg', 
        ST_GeomFromText('POINT(79.0045 30.6510)', 4326), 
        NOW() - INTERVAL '1 hour', 
        'PENDING'
    ),
    (
        2, 
        NULL, -- Pedestrian littering incident
        'Littering', 
        'Medium', 
        '/evidence/violations/pedestrian_litter_01.jpg', 
        ST_GeomFromText('POINT(79.4912 30.7405)', 4326), 
        NOW() - INTERVAL '45 minutes', 
        'PENDING'
    ),
    (
        3, 
        'MH12DE4321', 
        'Restricted_Zone_Entry', 
        'High', 
        '/evidence/violations/mh12de4321_restricted.jpg', 
        ST_GeomFromText('POINT(78.9402 30.9898)', 4326), 
        NOW() - INTERVAL '15 minutes', 
        'PENDING'
    )
ON CONFLICT DO NOTHING;

-- Seed IoT Sensor Telemetry Data
INSERT INTO iot_telemetry (location_id, device_id, pm25, pm10, aqi, temperature, humidity, co2, water_ph, measured_at)
VALUES
    (1, 'IOT-GK-A1', 12.5, 24.8, 38, 14.5, 62.0, 410.0, 7.2, NOW() - INTERVAL '15 minutes'),
    (1, 'IOT-GK-A1', 14.2, 28.1, 42, 14.1, 63.5, 415.0, 7.3, NOW() - INTERVAL '5 minutes'),
    (2, 'IOT-BD-B1', 8.4, 15.2, 25, 8.2, 55.0, 395.0, 7.8, NOW() - INTERVAL '20 minutes'),
    (2, 'IOT-BD-B1', 9.1, 16.8, 28, 7.9, 56.4, 398.0, 7.7, NOW() - INTERVAL '10 minutes'),
    (3, 'IOT-GT-C1', 6.0, 11.4, 18, 5.4, 48.0, 385.0, 8.1, NOW() - INTERVAL '10 minutes')
ON CONFLICT DO NOTHING;
