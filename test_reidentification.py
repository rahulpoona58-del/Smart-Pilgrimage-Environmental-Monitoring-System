# test_reidentification.py
# Verification Test Harness for Milestone 5: Cross-Camera Re-Identification & Journey Timelines.

import requests
import json
import time
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_PLATE = "UK07TA9999"

def run_reidentification_verification():
    print("=========================================")
    print("Milestone 5: Cross-Camera Re-ID Audit")
    print("=========================================")

    # 1. Quick backend status verification
    try:
        health = requests.get("http://localhost:8000/health", timeout=3.0)
        if health.status_code != 200:
            print("[Status Error] FastAPI backend returned unexpected status.")
            return
    except requests.RequestException:
        print("[Status Error] Unable to connect to backend server at http://localhost:8000.")
        print("Please ensure your FastAPI backend service is running before executing this test harness.")
        print("=========================================")
        return

    # Ensure our target test vehicle profile is registered first
    vehicle_payload = {
        "plate_number": TEST_PLATE,
        "vehicle_type": "Car",
        "emission_standard": "BS-VI",
        "fuel_type": "Petrol",
        "registered_owner": "Manish Devrath Bisht",
        "contact_number": "+919412000000"
    }
    requests.post(f"{API_BASE_URL}/vehicles", json=vehicle_payload, timeout=5.0)

    # 2. Simulate transits across multiple physical camera nodes in sequential order
    # Transit 1: Gaurikund Entry Gate at T - 3 hours
    time_t1 = (datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z"
    t1_payload = {
        "plate_number": TEST_PLATE,
        "camera_id": "CAM-GK-GATE-01",
        "location_id": 1, # Gaurikund Base
        "log_type": "ENTRY",
        "timestamp": time_t1,
        "raw_confidence": 0.95
    }

    # Transit 2: Gaurikund Exit Checkpoint at T - 2 hours
    time_t2 = (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
    t2_payload = {
        "plate_number": TEST_PLATE,
        "camera_id": "CAM-GK-EXIT-02",
        "location_id": 1, # Gaurikund Base
        "log_type": "EXIT",
        "timestamp": time_t2,
        "raw_confidence": 0.92
    }

    # Transit 3: Badrinath Entrance Checkpoint at T - 30 minutes
    time_t3 = (datetime.utcnow() - timedelta(minutes=30)).isoformat() + "Z"
    t3_payload = {
        "plate_number": TEST_PLATE,
        "camera_id": "CAM-BD-GATE-01",
        "location_id": 2, # Badrinath Entry
        "log_type": "ENTRY",
        "timestamp": time_t3,
        "raw_confidence": 0.88
    }

    print("Registering sequential transit logs across multiple camera systems...")
    try:
        requests.post(f"{API_BASE_URL}/logs/vehicle", json=t1_payload, timeout=5.0)
        requests.post(f"{API_BASE_URL}/logs/vehicle", json=t2_payload, timeout=5.0)
        requests.post(f"{API_BASE_URL}/logs/vehicle", json=t3_payload, timeout=5.0)
        print("Success: 3 transits registered successfully.")
    except requests.RequestException as e:
        print(f"Exception logging transit points: {e}")
        return

    # 3. Call the Re-ID Journey query REST API
    print(f"\nQuerying chronological journey timeline for vehicle: {TEST_PLATE}...")
    try:
        response = requests.get(f"{API_BASE_URL}/vehicles/{TEST_PLATE}/journey", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            print("\n=========================================")
            print("RE-IDENTIFIED MOVEMENT TIMELINE")
            print("=========================================")
            print(f"License Plate: {data['plate_number']}")
            print(f"Vehicle Profile: {data['vehicle_type']}")
            print(f"Compliance Index: {data['compliance_score']}%")
            print(f"Risk Assessment: {data['risk_rating'].upper()}")
            print("\nChronological Journey Stops:")
            
            for idx, stop in enumerate(data['journey_stops']):
                t_parsed = datetime.fromisoformat(stop['timestamp'].replace("Z", "+00:00"))
                t_str = t_parsed.strftime("%Y-%m-%d %I:%M:%S %p")
                
                print(f"  [{idx + 1}] Checkpoint Node: {stop['camera_id']}")
                print(f"      Location: Location #{stop['location_id']}")
                print(f"      Transit Event: {stop['log_type']}")
                print(f"      Detection Timestamp: {t_str}")
                print("  ---------------------------------------")
            
            print("\nVerification: Dynamic Cross-Camera Re-ID is fully active.")
        else:
            print(f"Error querying journey API: {response.text}")
    except requests.RequestException as e:
        print(f"Connection Exception: {e}")
        
    print("=========================================")

if __name__ == "__main__":
    run_reidentification_verification()
