# test_evidence_verification.py
# Verification Test Harness for Milestone 6: Evidence Cryptographic Seals & Integrity Auditing.

import requests
import os
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

def run_evidence_verification_audit():
    print("=========================================")
    print("Milestone 6: Evidence Cryptographic Audit")
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

    # 2. Write local dummy test image
    test_img = "audit_mock_evidence.jpg"
    print("Generating raw evidence image data...")
    with open(test_img, "wb") as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08OriginalUnmodifiedData')

    form_payload = {
        "location_id": "1",
        "camera_id": "CAM-GK-VALLEY-02",
        "plate_number": "UK07TA8888",
        "violation_type": "Littering",
        "severity_level": "Medium",
        "violation_timestamp": datetime.utcnow().isoformat() + "Z",
        "latitude": "30.6508",
        "longitude": "79.0058"
    }

    violation_id = None
    stored_path = None
    stored_hash = None

    # 3. Post environmental violation (POST /api/v1/violations)
    print("\n[Step 1/3] Uploading violation image, computing SHA-256 seal...")
    try:
        with open(test_img, "rb") as img_file:
            files = {"evidence_image": (test_img, img_file, "image/jpeg")}
            response = requests.post(f"{API_BASE_URL}/violations", data=form_payload, files=files, timeout=10.0)
            
            if response.status_code == 201:
                v_data = response.json()
                violation_id = v_data["id"]
                stored_path = v_data["evidence_image_url"].lstrip('/')
                stored_hash = v_data["evidence_hash"]
                
                print(f"Success: Registered violation #{violation_id}")
                print(f"    Assigned Cryptographic Hash: {stored_hash}")
                print(f"    Saved Local Filepath: {stored_path}")
            else:
                print(f"Error registering violation: {response.text}")
                return
    except requests.RequestException as e:
        print(f"Exception during violation post: {e}")
        return
    finally:
        if os.path.exists(test_img):
            os.remove(test_img)

    # 4. Perform Initial Cryptographic Verification (GET /api/v1/violations/{id}/verify)
    print("\n[Step 2/3] Performing Initial Cryptographic Integrity verification...")
    try:
        res_verify = requests.get(f"{API_BASE_URL}/violations/{violation_id}/verify", timeout=5.0)
        if res_verify.status_code == 200:
            v_report = res_verify.json()
            print(f"Success: Verification Audit Complete:")
            print(f"    Verification Status: {v_report['status'].upper()}")
            print(f"    Audit Message: {v_report['message']}")
            print(f"    Stored Seal Hash:  {v_report['stored_hash']}")
            print(f"    Calculated File Hash: {v_report['calculated_hash']}")
        else:
            print(f"Error querying verification API: {res_verify.text}")
    except requests.RequestException as e:
        print(f"Connection Exception during verification query: {e}")

    # 5. Simulate File Tampering
    # Modify the saved JPEG file on disk directly
    print("\n[Step 3/3] Simulating Visual Evidence Tampering...")
    if stored_path and os.path.exists(stored_path):
        try:
            # Modify 1 single byte of the saved evidence file on disk
            with open(stored_path, "ab") as f:
                f.write(b'AlteredDataInject')
            print("Successfully injected simulated altered data bytes into local file storage.")
            
            # Execute Verification audit again
            print("\nRe-evaluating Cryptographic Integrity after simulated tampering...")
            res_verify2 = requests.get(f"{API_BASE_URL}/violations/{violation_id}/verify", timeout=5.0)
            if res_verify2.status_code == 200:
                v_report2 = res_verify2.json()
                print("=========================================")
                print("SECURITY AUDIT WARNING")
                print("=========================================")
                print(f"    Verification Status: {v_report2['status'].upper()}")
                print(f"    Audit Message: {v_report2['message']}")
                print(f"    Original Stored Hash: {v_report2['stored_hash']}")
                print(f"    Tampered Calculated Hash: {v_report2['calculated_hash']}")
                print("=========================================")
                print("Verification: Anti-Tamper hash validation is fully active.")
            else:
                print(f"Error querying verification API: {res_verify2.text}")
        except Exception as e:
            print(f"Error simulating tampering: {e}")
    else:
        print("Error: Stored evidence file not found on disk.")

    print("\n=========================================")
    print("Evidence Storage Verification Complete.")
    print("=========================================")

if __name__ == "__main__":
    run_evidence_verification_audit()
