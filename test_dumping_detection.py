# test_dumping_detection.py
# Verification Test Harness for Milestone 9: Illegal Dumping & River Pollution Detection Engine.

import cv2
import numpy as np
import time
import os
import requests
from datetime import datetime

# Import modular dumping detector class
from edge.cv_pipelines.dumping_detector import DumpingDetector

class DumpingOrchestrator:
    """
    Orchestrates the real-time illegal dumping and river pollution analysis pipeline.
    Runs spatial-temporal heuristics on visual tracking frames, extracts evidence JPGs,
    and automatically uploads geolocated violation tickets to the FastAPI backend DB.
    """
    def __init__(self, api_url: str = "http://localhost:8000/api/v1/violations"):
        self.api_url = api_url
        # Instantiate detector: short stationary frame limit for rapid local testing
        self.detector = DumpingDetector(distance_threshold_pixels=100.0, stationary_frame_limit=4, pile_area_threshold=2000.0)
        self.camera_id = "CAM-GK-RIVER-04"
        self.location_id = 1 # Gaurikund Base default
        
        # Camera placement georeference
        self.camera_lat = 30.6508
        self.camera_lng = 79.0058

        # Define geofenced zones
        self.river_zones = [
            {
                "id": "RIVER-MANDAKINI-ZONE",
                "polygon": [(0, 300), (640, 300), (640, 480), (0, 480)] # Bottom half of the frame represents the river
            }
        ]
        
        self.bin_zones = [
            {
                "id": "BIN-COLLECTION-POINT-A",
                "polygon": [(50, 50), (200, 50), (200, 200), (50, 200)] # Top-left bin zone
            }
        ]

    def generate_violation_ticket(self, violation: dict):
        """Generates visual evidence keys and POSTs multi-part data directly to central FastAPI DB."""
        print(f"\n[Dumping Infraction Flagged] Generating Legal Evidence for: {violation['violation_type']}...")
        
        # 1. Create a timestamped evidence filename
        timestamp_str = datetime.utcnow().isoformat() + "Z"
        filename = f"dumping_incident_{int(time.time())}_{violation['violation_type'].lower()}.jpg"
        evidence_dir = "data/evidence"
        os.makedirs(evidence_dir, exist_ok=True)
        img_path = os.path.join(evidence_dir, filename)

        # 2. Save evidence frame JPG with overlays
        frame = violation["evidence_frame"]
        cv2.imwrite(img_path, frame)
        print(f"[Evidence Generated] Incident snapshot written: {img_path}")

        # 3. Compile multi-part API request payload
        form_payload = {
            "location_id": str(self.location_id),
            "camera_id": self.camera_id,
            "plate_number": violation["associated_plate"] if violation["associated_plate"] else "",
            "violation_type": violation["violation_type"],
            "severity_level": violation["severity_level"],
            "violation_timestamp": timestamp_str,
            "latitude": f"{violation['geotag'][0]:.6f}",
            "longitude": f"{violation['geotag'][1]:.6f}"
        }

        # 4. Post ticket to backend violations endpoint
        try:
            print(f"[API Dispatch] Posting ticket to DB... Coordinates: [{form_payload['latitude']}, {form_payload['longitude']}]")
            with open(img_path, "rb") as img_file:
                files = {"evidence_image": (filename, img_file, "image/jpeg")}
                response = requests.post(self.api_url, data=form_payload, files=files, timeout=10.0)
                
                if response.status_code == 201:
                    v_data = response.json()
                    print(f"[Violation Registered Successfully] DB Ticket ID: #{v_data['id']}")
                    print(f"    Assigned Fine: ₹{v_data['fine_amount_inr']}")
                    print(f"    Cryptographic Admissibility Hash: {v_data['evidence_hash']}")
                    print(f"    Evidence URL: http://localhost:8000{v_data['evidence_image_url']}")
                else:
                    print(f"[API Ingest Error] Failed to post violation: {response.text}")
        except requests.RequestException as e:
            print(f"[API Connect Exception] Backend API unreachable: {e}")

    def run_dumping_simulation(self):
        """Simulates sequence containing open dumping (growing pile) and river pollution."""
        print("=========================================")
        print("Illegal Dumping Action Detection Engine")
        print("=========================================")

        width, height = 640, 480
        
        # --------------------------------------------------------------------
        # INCIDENT 1: Geofenced River Pollution Simulation
        # --------------------------------------------------------------------
        print("\n--- Simulating Incident 1: River Pollution (Waterbody Intrusion) ---")
        
        # Simulated timeline: waste item (bottle class) falls into the river zone
        for frame_idx in range(12):
            frame = np.ones((height, width, 3), dtype=np.uint8) * 90
            
            # Draw river zone (blue overlay on bottom half)
            cv2.rectangle(frame, (0, 300), (640, 480), (255, 100, 0), -1)
            cv2.putText(frame, "GEOFENCED RIVER WATERBODY ZONE", (20, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Frame 0 to 4: Waste falls down
            if frame_idx < 5:
                wx, wy = 300, 180 + frame_idx * 25
            # Frame 5 to 11: Hits water and stays stationary at (300, 350)
            else:
                wx, wy = 300, 350

            # Paint the waste item (red circle)
            cv2.circle(frame, (wx, wy), 10, (0, 0, 255), -1)
            cv2.putText(frame, "PLASTIC BOTTLE ID: 801", (wx - 20, wy - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            waste = [{
                "track_id": 801,
                "bbox": (wx - 10, wy - 10, wx + 10, wy + 10),
                "class_name": "bottle"
            }]

            violations = self.detector.analyze_waste(
                detected_waste=waste,
                frame=frame,
                river_zones=self.river_zones,
                designated_bin_zones=self.bin_zones,
                camera_coords=(self.camera_lat, self.camera_lng)
            )

            for v in violations:
                self.generate_violation_ticket(v)
            
            time.sleep(0.05)

        # --------------------------------------------------------------------
        # INCIDENT 2: Open Dumping & Garbage Pile Growth Simulation
        # --------------------------------------------------------------------
        print("\n--- Simulating Incident 2: Bulk Open Dumping & Growing Garbage Pile ---")
        
        # Reset registry to avoid track confusion
        self.detector.waste_trajectories.clear()
        self.detector.logged_violations.clear()

        # Simulated timeline: waste pile placed outside bin, growing in size
        for frame_idx in range(12):
            frame = np.ones((height, width, 3), dtype=np.uint8) * 90
            
            # Draw designated bin zone (green overlay on top-left)
            cv2.rectangle(frame, (50, 50), (200, 200), (0, 180, 0), 2)
            cv2.putText(frame, "DESIGNATED BIN ZONE", (55, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 180, 0), 1)

            # Bounding box coordinates represent garbage pile placed at bottom right (450, 380)
            # Frame 0 to 4: Initial pile size is small (40x40 pixels)
            if frame_idx < 5:
                pw, ph = 40, 40
            # Frame 5 to 11: Dynamic growth occurs (reaches 90x90 pixels, simulating dynamic garbage pile expansion)
            else:
                pw, ph = 90, 90

            px1, py1 = 450 - pw//2, 380 - ph//2
            px2, py2 = 450 + pw//2, 380 + ph//2

            # Paint growing garbage pile (brown box)
            cv2.rectangle(frame, (px1, py1), (px2, py2), (42, 42, 165), -1)
            cv2.putText(frame, "GROWING OPEN DUMPING PILE ID: 902", (px1 - 20, py1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (42, 42, 165), 1)

            waste = [{
                "track_id": 902,
                "bbox": (px1, py1, px2, py2),
                "class_name": "garbage_pile"
            }]

            violations = self.detector.analyze_waste(
                detected_waste=waste,
                frame=frame,
                river_zones=self.river_zones,
                designated_bin_zones=self.bin_zones,
                camera_coords=(self.camera_lat, self.camera_lng)
            )

            for v in violations:
                self.generate_violation_ticket(v)
            
            time.sleep(0.05)

        print("\n=========================================")
        print("Dumping Detection Heuristics Verification Complete.")
        print("=========================================")

if __name__ == "__main__":
    orchestrator = DumpingOrchestrator()
    orchestrator.run_dumping_simulation()
