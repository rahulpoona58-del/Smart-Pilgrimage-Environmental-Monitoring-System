# test_disaster_monitoring.py
# Verification harness for SPEMS Disaster Monitoring Module.

import pytest
import numpy as np
import cv2
import io
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.app.main import app
from backend.app.core.disaster import DisasterMonitoringService

def test_optical_flow_calculation():
    # 1. Test identical frames (zero flow)
    frame1 = np.zeros((100, 100), dtype=np.uint8)
    frame2 = np.zeros((100, 100), dtype=np.uint8)
    flow = DisasterMonitoringService.calculate_optical_flow(frame1, frame2)
    assert flow == 0.0

    # 2. Test frame with motion (shift white box)
    frame1_motion = np.zeros((100, 100), dtype=np.uint8)
    frame1_motion[20:40, 20:40] = 255
    frame2_motion = np.zeros((100, 100), dtype=np.uint8)
    frame2_motion[40:60, 40:60] = 255
    
    flow_motion = DisasterMonitoringService.calculate_optical_flow(frame1_motion, frame2_motion)
    assert flow_motion > 0.0

def test_disaster_monitoring_endpoints():
    with TestClient(app) as client:
        # 1. Post telemetry logs to trigger flood monitoring conditions
        telemetry_payload = {
            "location_id": 1,
            "device_id": "TEST-G-01",
            "pm25": 10.0,
            "pm10": 15.0,
            "aqi": 35,
            "temperature": 12.0,
            "humidity": 97.0, # High moisture proxy for flood evaluation
            "co2": 450.0,
            "water_ph": 4.5, # Acidic pH runoff anomaly
            "measured_at": datetime.now(timezone.utc).isoformat()
        }
        tel_res = client.post("/api/v1/telemetry", json=telemetry_payload)
        assert tel_res.status_code == 201

        # 2. Query status for location 1
        status_res = client.get("/api/v1/disaster/status/1")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["location_id"] == 1
        assert "landslide_risk_score" in status_data
        assert "flood_risk_score" in status_data
        assert "overall_hazard_index" in status_data
        assert "status" in status_data
        
        # Verify status is escalated due to water pH anomalies and high humidity
        assert status_data["status"] in ["WARNING", "CRITICAL"]

        # 3. Retrieve active disaster alerts
        alerts_res = client.get("/api/v1/disaster/alerts")
        assert alerts_res.status_code == 200
        alerts_list = alerts_res.json()
        assert len(alerts_list) > 0
        
        target_alert = alerts_list[0]
        assert target_alert["hazard_type"] == "Flood"
        assert target_alert["is_active"] is True
        
        # 4. Resolve alert
        resolve_res = client.post(f"/api/v1/disaster/alerts/{target_alert['id']}/resolve")
        assert resolve_res.status_code == 200
        resolved_alert = resolve_res.json()
        assert resolved_alert["is_active"] is False
        assert resolved_alert["resolved_at"] is not None

        # 5. Evaluate frames via multipart endpoints (simulating real cctv feed input)
        # Convert frames to bytes
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        for i in range(100):
            img1[:, i] = int(i * 2.5)
        img2 = np.roll(img1, 3, axis=1)
        
        _, img1_encoded = cv2.imencode(".png", img1)
        _, img2_encoded = cv2.imencode(".png", img2)
        
        files = {
            "prev_frame": ("frame1.png", io.BytesIO(img1_encoded.tobytes()), "image/png"),
            "curr_frame": ("frame2.png", io.BytesIO(img2_encoded.tobytes()), "image/png")
        }
        
        eval_res = client.post(
            "/api/v1/disaster/evaluate/1?camera_id=CAM-GK-RIVER-04", 
            files=files
        )
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["landslide_risk_score"] > 10.0 # Motion detected

        print("\n[Disaster Monitoring Test Success] Validation details:")
        print(f"  - Landslide Risk Score: {eval_data['landslide_risk_score']}")
        print(f"  - Flood Risk Score: {status_data['flood_risk_score']}")
        print(f"  - Status Escalation: {status_data['status']}")
        print(f"  - Resolved Alert ID: {target_alert['id']}")

if __name__ == "__main__":
    test_optical_flow_calculation()
    test_disaster_monitoring_endpoints()
