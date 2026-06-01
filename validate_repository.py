# validate_repository.py
# System Integrity Validator: Confirms structural completeness of all SPEMS files.

import os

# Define complete target file tree generated in previous phases
REQUIRED_FILES = [
    # Root configs
    "requirements.txt",
    "setup_env.ps1",
    "run_mvp.py",
    
    # Testing / Dry Run modules
    "test_setup.py",
    "test_opencv.py",
    "test_vehicle_tracking.py",
    "test_littering_detection.py",
    "test_violation_apis.py",
    
    # Database
    "database/schema.sql",
    "database/seed_data.sql",
    
    # Backend
    "backend/requirements.txt",
    "backend/Dockerfile",
    "backend/app/main.py",
    "backend/app/db/session.py",
    "backend/app/db/models.py",
    "backend/app/schemas/types.py",
    "backend/app/api/v1/endpoints/violations.py",
    "backend/app/api/v1/endpoints/vehicles.py",
    "backend/app/api/v1/endpoints/cameras.py",
    "backend/app/api/v1/endpoints/compliance.py",
    
    # Frontend
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/next.config.js",
    "frontend/Dockerfile",
    "frontend/src/styles/globals.css",
    "frontend/src/components/DashboardMap.tsx",
    "frontend/src/components/ViolationsFeed.tsx",
    "frontend/src/components/TelemetryCharts.tsx",
    "frontend/src/pages/index.tsx",
    
    # Edge AI
    "edge/cv_pipelines/vehicle_tracker.py",
    "edge/cv_pipelines/anpr_engine.py",
    "edge/cv_pipelines/litter_detector.py",
    "edge/utils/failsafe_buffer.py",
    "edge/config.yaml",
    "edge/main_edge.py",
    "edge/README.md",
    
    # Cloud AI & Simulators
    "ai_services/drone_processor/main.py",
    "data_simulators/mock_iot_sensors.py",
    
    # Infrastructure & DevOps
    "infra/kubernetes/backend-deployment.yaml",
    "infra/kubernetes/postgres-statefulset.yaml",
    "infra/kubernetes/ingress.yaml",
    "infra/prometheus/prometheus.yml"
]

def verify_system_integrity():
    print("==================================================")
    print("      🕉️  SPEMS - COMPONENT INTEGRITY AUDIT  🕉️   ")
    print("==================================================")
    print("Scanning active workspace folder structures...")
    
    missing_count = 0
    success_count = 0
    
    for f in REQUIRED_FILES:
        if os.path.exists(f):
            print(f"[VERIFIED] File present: {f}")
            success_count += 1
        else:
            print(f"[MISSING] Required component absent: {f}")
            missing_count += 1
            
    print("==================================================")
    print(f"Validation summary: Present={success_count}/{len(REQUIRED_FILES)} Missing={missing_count}")
    
    if missing_count == 0:
        print("RESULT: Component integrity check successful. Repository is fully built.")
    else:
        print("RESULT: Component integrity check failed. Some components are missing.")
    print("==================================================")

if __name__ == "__main__":
    verify_system_integrity()
