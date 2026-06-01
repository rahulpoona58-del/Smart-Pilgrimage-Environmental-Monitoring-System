# test_violation_apis.py
# Verification Test Harness for the PostgreSQL CRUD Storage System.

import requests
import os
import time
import sys
from datetime import datetime, timezone

# Prevent Unicode encoding issues in Windows command prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE_URL = "http://localhost:8000/api/v1"

def run_storage_verification_tests():
    print("=========================================")
    print("Violation Storage System: REST API Testing")
    print("=========================================")

    # Quick online check before initiating API request loops
    try:
        health = requests.get("http://localhost:8000/health", timeout=3.0)
        if health.status_code == 200:
            print("[Status OK] Central FastAPI backend is active and reachable.")
        else:
            print(f"[Status Error] Received unexpected status code: {health.status_code}")
            return
    except requests.RequestException:
        print("[Status Error] Unable to connect to backend server at http://localhost:8000.")
        print("Please ensure your FastAPI backend service is running before executing this test harness.")
        print("=========================================")
        return

    # ----------------------------------------------------------------------------
    # 1. REGISTER CAMERAS (CRUD - POST)
    # ----------------------------------------------------------------------------
    cam_payload = {
        "id": "CAM-GK-TEST-99",
        "location_id": 1, # Gaurikund Base default
        "model_name": "Hikvision Outdoor PTZ 4K",
        "rtsp_url": "rtsp://internal-ip-mock/live",
        "latitude": 30.6502,
        "longitude": 79.0052
    }
    
    print("\n[Test 1/4] Registering Camera Node...")
    try:
        res_cam = requests.post(f"{API_BASE_URL}/cameras", json=cam_payload, timeout=5.0)
        if res_cam.status_code == 201:
            print(f"Success: Registered Camera ID: {res_cam.json()['id']}")
        elif res_cam.status_code == 400:
            print(f"Informational: Camera ID already present. Skipping registration.")
        else:
            print(f"Error registering camera: {res_cam.text}")
    except requests.RequestException as e:
        print(f"Connection Exception during camera registration: {e}")

    # ----------------------------------------------------------------------------
    # 2. REGISTER VEHICLES (CRUD - POST)
    # ----------------------------------------------------------------------------
    vehicle_payload = {
        "plate_number": "UK07TA9999",
        "vehicle_type": "SUV",
        "emission_standard": "BS-VI",
        "fuel_type": "Petrol",
        "registered_owner": "Manish Devrath Bisht",
        "contact_number": "+919412000000"
    }

    print("\n[Test 2/4] Registering Vehicle Profile...")
    try:
        res_v = requests.post(f"{API_BASE_URL}/vehicles", json=vehicle_payload, timeout=5.0)
        if res_v.status_code == 201:
            print(f"Success: Registered Vehicle Plate: {res_v.json()['plate_number']} (Owner: {res_v.json()['registered_owner']})")
        elif res_v.status_code == 400:
            print(f"Informational: Vehicle Plate already present. Skipping profile creation.")
        else:
            print(f"Error registering vehicle: {res_v.text}")
    except requests.RequestException as e:
        print(f"Connection Exception during vehicle registration: {e}")

    # ----------------------------------------------------------------------------
    # 3. REPORT ENVIRONMENTAL VIOLATIONS WITH EVIDENCE UPLOAD (CRUD - POST)
    # ----------------------------------------------------------------------------
    print("\n[Test 3/4] Posting Violation & Uploading Evidence Image...")
    
    # Create local temporary dummy image file to represent evidence frame
    dummy_img_path = "temp_mock_evidence.jpg"
    with open(dummy_img_path, "wb") as f:
        # Simple blank byte layout representing image
        import os
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08' + os.urandom(16))

    form_payload = {
        "location_id": "1",
        "camera_id": "CAM-GK-TEST-99",
        "plate_number": "UK07TA9999",
        "violation_type": "Littering",
        "severity_level": "Medium",
        "violation_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "latitude": "30.6504",
        "longitude": "79.0054"
    }

    try:
        with open(dummy_img_path, "rb") as img_file:
            files = {"evidence_image": (dummy_img_path, img_file, "image/jpeg")}
            res_violation = requests.post(
                f"{API_BASE_URL}/violations", 
                data=form_payload, 
                files=files, 
                timeout=10.0
            )
            
            if res_violation.status_code == 201:
                v_data = res_violation.json()
                print(f"Success: Environmental Violation Logged (ID: {v_data['id']})")
                print(f"    Type: {v_data['violation_type']}")
                print(f"    Assigned Fine: ₹{v_data['fine_amount_inr']}")
                print(f"    Evidence URL: {v_data['evidence_image_url']}")
            else:
                print(f"Error registering violation event: {res_violation.text}")
    except requests.RequestException as e:
        print(f"Connection Exception during violation reporting: {e}")
    finally:
        # Clean up temporary mock image
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

    # ----------------------------------------------------------------------------
    # 4. QUERY ACTIVE VIOLATIONS (CRUD - GET)
    # ----------------------------------------------------------------------------
    print("\n[Test 4/4] Querying Active Violations Feed...")
    try:
        res_list = requests.get(f"{API_BASE_URL}/violations", timeout=5.0)
        if res_list.status_code == 200:
            active_list = res_list.json()
            print(f"Success: Retrieved {len(active_list)} active violations from PostgreSQL DB:")
            for item in active_list[:3]: # Print latest 3
                print(f"  - ID {item['id']}: [{item['violation_type']}] Vehicle: {item['plate_number']} Status: {item['status']}")
        else:
            print(f"Error querying violations feed: {res_list.text}")
    except requests.RequestException as e:
        print(f"Connection Exception during violations retrieval: {e}")

    print("\n=========================================")
    print("Storage Verification Harness Complete.")
    print("=========================================")

if __name__ == "__main__":
    run_storage_verification_tests()
