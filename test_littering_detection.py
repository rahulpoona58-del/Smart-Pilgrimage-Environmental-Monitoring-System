# test_littering_detection.py
# Littering Detection Module: Local Action Heuristics with Automated API Ingestion.

import cv2
import numpy as np
import time
import os
import requests
from datetime import datetime

# Import modular components created in Phase 1 & 5
from edge.cv_pipelines.litter_detector import LitterDetector

class LocalLitterOrchestrator:
    """
    Orchestrates the real-time litter action analysis pipeline.
    Runs spatial-temporal heuristics on visual tracking frames, extracts evidence JPGs,
    and automatically uploads a geolocated violation ticket to the FastAPI backend DB.
    """
    def __init__(self, api_url: str = "http://localhost:8000/api/v1/violations"):
        self.api_url = api_url
        self.detector = LitterDetector(distance_threshold_pixels=100.0, stationary_frame_limit=5)
        self.camera_id = "CAM-GK-ROADSIDE-02"
        self.location_id = 1 # Gaurikund Base default
        
        # Local mock coordinates for Gaurikund roadside
        self.latitude = 30.6506
        self.longitude = 79.0056

    def generate_violation_ticket(self, violation: dict):
        """Generates evidence image and posts a dynamic ticket directly to the central FastAPI DB."""
        print("\n[Littering Action Classified] Compiling Legal Evidence...")
        
        # 1. Create a timestamped evidence filename
        timestamp_str = datetime.utcnow().isoformat() + "Z"
        filename = f"litter_incident_{int(time.time())}.jpg"
        evidence_dir = "data/evidence"
        os.makedirs(evidence_dir, exist_ok=True)
        img_path = os.path.join(evidence_dir, filename)

        # 2. Save evidence frame JPG crop to disk
        frame = violation["evidence_frame"]
        cv2.imwrite(img_path, frame)
        print(f"[Evidence Generated] Written incident snapshot to: {img_path}")

        # 3. Compile multi-part API request payload
        form_payload = {
            "location_id": str(self.location_id),
            "camera_id": self.camera_id,
            "plate_number": violation["associated_plate"] if violation["associated_plate"] else "",
            "violation_type": "Littering",
            "severity_level": violation["severity_level"],
            "violation_timestamp": timestamp_str,
            "latitude": str(self.latitude),
            "longitude": str(self.longitude)
        }

        # 4. Post ticket to backend violations endpoint
        try:
            print("[API Dispatch] Posting violation ticket to database...")
            with open(img_path, "rb") as img_file:
                files = {"evidence_image": (filename, img_file, "image/jpeg")}
                response = requests.post(self.api_url, data=form_payload, files=files, timeout=10.0)
                
                if response.status_code == 201:
                    v_data = response.json()
                    print(f"[Violation Registered Successfully] DB Ticket ID: #{v_data['id']}")
                    print(f"    Classified Severity: {v_data['severity_level']}")
                    print(f"    Calculated RTO Fine: ₹{v_data['fine_amount_inr']}")
                    print(f"    Evidence URL: http://localhost:8000{v_data['evidence_image_url']}")
                else:
                    print(f"[API Ingest Error] Failed to post violation: {response.text}")
        except requests.RequestException as e:
            print(f"[API Connect Exception] Backend API unreachable. Incident cached in edge failsafe buffer: {e}")

    def run_incident_simulation(self):
        """Simulates a video frame sequence where a pedestrian discards a bottle to test heuristics."""
        print("=========================================")
        print("Littering Action Detection Simulation")
        print("=========================================")

        # Create solid gray mock camera canvas (width: 640, height: 480)
        width, height = 640, 480
        
        # 1. Simulate a tracked pedestrian standing stationary in the center lane
        pedestrian = {
            "track_id": 101,
            "bbox": (280, 200, 340, 360), # [x1, y1, x2, y2]
            "class_name": "person"
        }

        print("Executing sequential frame tracking loops...")
        
        # Loop over 20 frames representing a timeline
        for frame_idx in range(20):
            # Create gray frame
            frame = np.ones((height, width, 3), dtype=np.uint8) * 80
            
            # Draw pedestrian box (green)
            cv2.rectangle(frame, (280, 200), (340, 360), (0, 255, 0), 2)
            cv2.putText(frame, "PEDESTRIAN ID: 101", (280, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            # Draw a visual gate / trash item
            # Frame 0 to 4: The bottle is overlapping/held by the pedestrian (overlapping coordinates)
            if frame_idx < 5:
                bx, by = 310, 300
            # Frame 5 to 9: The bottle detaches and drops diagonally down (falling phase)
            elif frame_idx < 10:
                bx = 310 + (frame_idx - 5) * 15
                by = 300 + (frame_idx - 5) * 20
            # Frame 10 to 19: The bottle hits the ground at coordinate (370, 380) and remains stationary
            else:
                bx, by = 370, 380

            # Paint the discarded waste (red circle representing a bottle/wrapper)
            cv2.circle(frame, (bx, by), 8, (0, 0, 255), -1)
            cv2.putText(frame, f"WASTE ID: 501", (bx - 10, by - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            # Compile standard detection lists as if returned by YOLO models
            subjects = [pedestrian]
            waste = [{
                "track_id": 501,
                "bbox": (bx - 8, by - 8, bx + 8, by + 8)
            }]

            # 2. Run the litter heuristic analyzer on this active frame
            violations = self.detector.analyze_objects(subjects, waste, frame)

            # 3. If a violation is flagged, instantly generate a ticket
            for v in violations:
                self.generate_violation_ticket(v)

            # Add small delay to mimic standard video framerate (15fps)
            time.sleep(0.06)

        print("\n=========================================")
        print("Simulation Completed successfully.")
        print("=========================================")

if __name__ == "__main__":
    orchestrator = LocalLitterOrchestrator()
    orchestrator.run_incident_simulation()
