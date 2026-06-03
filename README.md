# Smart Pilgrimage Environmental Monitoring & Compliance System (SPEMS)

An enterprise-grade, hybrid edge-cloud AI system designed to monitor, score, and enforce environmental compliance across the high-altitude pilgrimage routes of Uttarakhand (Char Dham: Kedarnath, Badrinath, Gangotri, Yamunotri).

---

## 1. Project Directory Structure

```
smart-pilgrimage-ems/
├── database/                        # PostgreSQL schemas and migrations
│   └── schema.sql                   # SQL definition for spatial tables and indices
│
├── backend/                         # FastAPI application codebase
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # API endpoints, WebSockets, core loops
│   │   ├── config.py                # Environment configuration
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py           # SQLAlchemy session manager
│   │   │   └── models.py            # PostgreSQL SQLAlchemy models
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── types.py             # Pydantic validation schemas
│   │   └── core/
│   │       ├── __init__.py
│   │       ├── compliance.py        # Environmental scoring rules
│   │       └── notify.py            # Government notification dispatchers
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                        # React / Next.js Admin & Operations Dashboard
│   ├── pages/                       # Next.js pages and API routes
│   ├── components/                  # Custom dashboard components
│   ├── styles/                      # Responsive vanilla CSS styling
│   ├── package.json
│   └── Dockerfile
│
├── edge/                            # Edge AI services for deployment on NVIDIA Jetson
│   ├── cv_pipelines/
│   │   ├── vehicle_tracker.py       # YOLOv8 + ByteTrack object tracking
│   │   ├── anpr_engine.py           # Automatic Number Plate Recognition
│   │   └── litter_detector.py       # Garbage & action classification
│   ├── main_edge.py                 # Core local runner
│   └── config.yaml                  # Edge node stream & geofence parameters
│
├── infra/                           # Cloud deployment & monitoring configurations
│   ├── kubernetes/                  # Kubernetes manifests (deployments, ingress, pv)
│   └── prometheus/                  # Metrics scraping and alertmanager configuration
│
└── data_simulators/                 # Simulation engines for end-to-end local validation
    ├── mock_iot_sensors.py          # Weather & Air Quality telemetries generator
    └── mock_video_stream.py         # CCTV streaming simulator emitting virtual vehicles
```

---

## 2. Technical Philosophy & Design

- **Edge Resilience**: Operates local edge inferencing. Telemetries and violations are queued in a local SQLite/RocksDB buffer when internet connectivity is severed, then synced securely via HTTPS once link status is restored.
- **Geospatial Processing**: PostGIS handles geographic boundary tracking. Polygon coordinates represent restricted landslide-prone areas or green zones. If vehicles enter or park in these zones, violations are flagged automatically.
- **Dynamic Risk Matrix**: Evaluates vehicle health based on age, emission compliance, and historical route violations. Air quality indices (AQI) impact site risks in real-time, warning tourist bureaus when visitor inflow exceeds capacity limits.

---

## 3. Local Operational Instructions

### Step 1: Start Backend Orchestrator & Simulators
Execute the local MVP launcher script:
```powershell
python run_mvp.py
```
*Effect*: Starts the FastAPI backend (port 8000), IoT telemetry sensors generator, and Edge AI background monitors.

### Step 2: Build & Start Next.js Frontend Dashboard
Open a new terminal window, navigate to the `frontend/` directory, and launch the dev environment:
```bash
cd frontend
npm run dev
```
*Effect*: Starts the Next.js visual server at `http://localhost:3000`.

### Step 3: Run the Integrated Verification Pipeline
To test the vehicle tracking, ANPR character recognition, and geofencing systems using the pipeline verification harness:
```powershell
python test_integrated_pipeline.py
```
*Effect*: Automatically builds a simulated vehicle stream file, detects the car bounds, parses its license plate text (`UK07TA1230`), tracks its coordinates, flags a `Restricted_Zone_Entry` violation inside `ZONE-A-NO-PARK`, calculates a SHA-256 evidence seal, and posts the ticket to the running database API.

---

## 4. Visual Dashboard Features (Government Command Center)
- **Live CCTV Wall Matrix**: Supports a 2x2 grid displaying active video stream overlays alongside computer vision bounding boxes.
- **Uttarakhand GIS Corridor Map**: Visual path map displaying coordinate checkpoints (Gaurikund, Jungle Chatti, Rambara, Kedarnath), geofences, active violations, and PM2.5 heatmaps.
- **Telemetry Charts**: Plots hourly timelines for AQI/dust, CO2 standards, ambient air temperature, and river pH records.
- **Violation Auditing**: Supports cryptographic SHA-256 seal verification and e-challan ASCII report downloads directly from database logs.

