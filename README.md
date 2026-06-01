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
