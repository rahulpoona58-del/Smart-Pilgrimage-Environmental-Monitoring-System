# test_compliance_engine.py
# Verification Test Harness for Milestone 13: Environmental Compliance & Predictive Scoring Engine.

import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta, timezone

# Prevent Unicode encoding issues in Windows command prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE_URL = "http://localhost:8000/api/v1"

class ComplianceTestOrchestrator:
    """
    Orchestrates compliance evaluation audits against the central FastAPI engine.
    Seeds sequential violations to verify rolling repeat multipliers, AQI variations,
    and runs predictive risk algorithms.
    """
    def __init__(self):
        self.target_plate = "UK07TA8888"
        self.location_id = 1

    def run_compliance_audit(self):
        print("=========================================")
        print("Environmental Compliance Scoring Engine")
        print("=========================================")

        # A. Quick online check
        try:
            health = requests.get("http://localhost:8000/health", timeout=3.0)
            if health.status_code == 200:
                print("[Status OK] Central FastAPI backend is active and reachable.")
            else:
                print(f"[Status Error] Received unexpected status code: {health.status_code}")
                return
        except requests.RequestException:
            print("[Status Error]Central FastAPI backend offline. Please boot backend first.")
            return

        # B. Register Test Vehicle Profile
        print("\nStep 1: Registering Test Vehicle Profile...")
        vehicle_payload = {
            "plate_number": self.target_plate,
            "vehicle_type": "SUV",
            "emission_standard": "BS-VI",
            "fuel_type": "Petrol",
            "registered_owner": "Himalayan Ranger Team",
            "contact_number": "+919411000000"
        }
        res_v = requests.post(f"{API_BASE_URL}/vehicles", json=vehicle_payload, timeout=5.0)
        if res_v.status_code in [201, 400]:
            print(f"Vehicle plate {self.target_plate} successfully registered/present.")
        else:
            print(f"Error registering vehicle: {res_v.text}")
            return

        # C. Seed Multi-Day Chronological Violations to Test Multipliers
        print("\nStep 2: Seeding Chronological Violations to Verify Repeat Multipliers...")
        
        # Incident 1: Littering on Day 1 (Base deduction = 15)
        # Incident 2: Littering on Day 10 (Rolling repeat < 30 days, deduction = 15 * 1.5 = 22)
        # Incident 3: Littering on Day 20 (Second rolling repeat < 30 days, deduction = 15 * 2.0 = 30)
        # Expected Total Score: 100 - 15 - 22 - 30 = 33 (High Risk rating!)

        incidents = [
            {"type": "Littering", "days_ago": 20, "image": "litter1.jpg"},
            {"type": "Littering", "days_ago": 10, "image": "litter2.jpg"},
            {"type": "Littering", "days_ago": 1, "image": "litter3.jpg"}
        ]

        for idx, inc in enumerate(incidents):
            timestamp = (datetime.now(timezone.utc) - timedelta(days=inc["days_ago"])).isoformat() + "Z"
            
            # Create local temp dummy image
            dummy_img_path = f"temp_mock_{inc['image']}"
            with open(dummy_img_path, "wb") as f:
                f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08' + os.urandom(16))

            form_payload = {
                "location_id": str(self.location_id),
                "camera_id": "CAM-GK-ENTRY",
                "plate_number": self.target_plate,
                "violation_type": inc["type"],
                "severity_level": "Medium",
                "violation_timestamp": timestamp,
                "latitude": "30.6504",
                "longitude": "79.0054"
            }

            try:
                with open(dummy_img_path, "rb") as img_file:
                    files = {"evidence_image": (dummy_img_path, img_file, "image/jpeg")}
                    res_violation = requests.post(f"{API_BASE_URL}/violations", data=form_payload, files=files, timeout=10.0)
                    
                    if res_violation.status_code == 201:
                        print(f"  Incident #{idx+1} Seeded: [{inc['type']}] on Day -{inc['days_ago']}.")
                    else:
                        print(f"  Failed to seed incident #{idx+1}: {res_violation.text}")
            finally:
                if os.path.exists(dummy_img_path):
                    os.remove(dummy_img_path)

        # D. Query Dynamic Compliance Score Engine for Vehicle
        print("\nStep 3: Calculating Rolling Vehicle Eco Index...")
        res_score = requests.get(f"{API_BASE_URL}/compliance/vehicle/{self.target_plate}", timeout=5.0)
        if res_score.status_code == 200:
            score_data = res_score.json()
            print(f"Vehicle Compliance Audit Summary for {self.target_plate}:")
            print(f"  Composite Eco Score: {score_data['compliance_score']}/100")
            print(f"  Computed Risk Rating: {score_data['risk_rating']}")
            print(f"  Total Active Violations: {score_data['total_violations']}")
            for p in score_data['penalty_history']:
                print(f"    - Violation ID #{p['violation_id']}: Base={p['base_penalty']} Multiplier={p['multiplier']}x (Deducted: -{p['deduction']})")
        else:
            print(f"Error calling vehicle compliance score: {res_score.text}")

        # E. Query Dynamic Location Green Index
        print("\nStep 4: Evaluating Gaurikund Checkpoint Green Index...")
        res_loc = requests.get(f"{API_BASE_URL}/compliance/location/{self.location_id}", timeout=5.0)
        if res_loc.status_code == 200:
            loc_data = res_loc.json()
            print(f"Checkpoint Green Index Summary for location {self.location_id} ({loc_data['location_name']}):")
            print(f"  Composite Green Index: {loc_data['composite_green_index']}/100")
            print(f"  Breakdown Analytics:")
            print(f"    - Air Quality Score: {loc_data['breakdown']['air_quality_score']} (24h Avg AQI: {loc_data['breakdown']['avg_24h_aqi']})")
            print(f"    - Waste Compliance Score: {loc_data['breakdown']['waste_compliance_score']} (Uncleared Infractions: {loc_data['breakdown']['recent_violations_count']})")
            print(f"    - Crowd Congestion Score: {loc_data['breakdown']['crowd_congestion_score']}")
        else:
            print(f"Error calling location compliance score: {res_loc.text}")

        # F. Route Multi-Location average
        print("\nStep 5: Evaluating Char Dham Route Trail average Index...")
        res_route = requests.get(f"{API_BASE_URL}/compliance/route?location_ids=1&location_ids=2", timeout=5.0)
        if res_route.status_code == 200:
            r_data = res_route.json()
            print(f"Route Index calculated successfully across {r_data['locations_evaluated']} locations:")
            print(f"  Route Compliance Index: {r_data['route_compliance_index']}/100")
            for item in r_data['route_breakdown']:
                print(f"    - {item['name']}: {item['score']}/100")
        else:
            print(f"Error calling route compliance score: {res_route.text}")

        print("\n=========================================")
        print("Compliance Engine Verification Complete.")
        print("=========================================")

if __name__ == "__main__":
    orchestrator = ComplianceTestOrchestrator()
    orchestrator.run_compliance_audit()
