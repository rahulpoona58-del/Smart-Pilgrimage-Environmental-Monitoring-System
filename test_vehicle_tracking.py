# test_vehicle_tracking.py
# Refactored Tracking Module: Integrates multi-threaded ingestion, YOLOv8 tracking, and API fallbacks.

import cv2
import numpy as np
import time
import os
import requests
from datetime import datetime

# Import modular components created in Milestones 1 and 2
from edge.utils.camera_ingest import MultiCameraIngestManager
from edge.cv_pipelines.vehicle_tracker import VehicleTracker
from edge.utils.failsafe_buffer import FailsafeBuffer

class ResilientEdgeTracker:
    """
    Orchestrates real-time vehicle tracking at a localized gate.
    Consumes frames from the multi-threaded Ingestion Manager, tracks coordinates,
    checks virtual boundary crossings, and logs transits to backend APIs with SQLite backups.
    """
    def __init__(self, camera_id: str, stream_url: str, api_url: str = "http://127.0.0.1:8000/api/v1/logs/vehicle"):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.api_url = api_url
        self.location_id = 1 # Gaurikund Base default
        
        # Initialize modules
        self.ingest = MultiCameraIngestManager()
        self.tracker = VehicleTracker()
        self.buffer = FailsafeBuffer(db_path="database/buffer.db")
        
        # Register and boot streams
        self.ingest.register_camera(self.camera_id, self.stream_url)
        
        # Tracking states
        self.counted_ids = set()
        self.transit_count = 0
        self.active_tracks = {}

    def start(self):
        """Starts background ingestion stream."""
        self.ingest.start_all_streams()
        print(f"[Tracker] Ingestion stream active for node: {self.camera_id}")

    def stop(self):
        """Terminates background ingestion stream."""
        self.ingest.stop_all_streams()
        print(f"[Tracker] Ingestion stream stopped for node: {self.camera_id}")

    def log_transit(self, track_id: int, confidence: float):
        """Dispatches transit metadata to FastAPI backend with automated SQLite backup on connection failures."""
        timestamp_str = datetime.utcnow().isoformat() + "Z"
        virtual_plate = f"UK07TR{1000 + track_id}"
        
        payload = {
            "plate_number": virtual_plate,
            "camera_id": self.camera_id,
            "location_id": self.location_id,
            "log_type": "ENTRY",
            "timestamp": timestamp_str,
            "raw_confidence": confidence
        }

        # Attempt to upload to central API
        try:
            response = requests.post(self.api_url, json=payload, timeout=3.0)
            if response.status_code == 201:
                print(f"[API Success] Registered ENTRY for vehicle {virtual_plate} (Track ID: {track_id})")
                return
        except requests.RequestException:
            pass # Backend offline, fallback to SQLite cache
            
        # Offline caching fallback
        self.buffer.buffer_vehicle_log(
            plate=virtual_plate,
            camera_id=self.camera_id,
            location_id=self.location_id,
            log_type="ENTRY",
            timestamp=timestamp_str,
            confidence=confidence
        )

    def process_next_frame(self, line_y: int) -> np.ndarray:
        """Fetches the latest decoded frame from the worker queue and updates coordinates."""
        frame = self.ingest.fetch_frame(self.camera_id)
        if frame is None:
            return None

        # Draw dynamic virtual gate line (BGR: Cyan)
        cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (0, 240, 255), 2)
        cv2.putText(frame, "GATE BOUNDARY", (20, line_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 240, 255), 1, cv2.LINE_AA)

        # Execute YOLOv8 ByteTrack pipeline
        tracked_vehicles = self.tracker.detect_and_track(frame)

        for vehicle in tracked_vehicles:
            x1, y1, x2, y2 = vehicle["bbox"]
            track_id = vehicle["track_id"]
            class_name = vehicle["class_name"]
            conf = vehicle["confidence"]

            # Compute contact bottom center
            cx = (x1 + x2) // 2
            cy = y2

            # Visual overlay bounding boxes (BGR: Emerald Green)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (16, 185, 129), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.putText(frame, f"ID: {track_id} {class_name.upper()}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (16, 185, 129), 2)

            # Virtual Gate crossing calculation
            if cy > line_y and track_id not in self.counted_ids:
                self.counted_ids.add(track_id)
                self.transit_count += 1
                
                # Log log details asynchronously
                self.log_transit(track_id, conf)

        # Draw vehicle counter overlay
        cv2.rectangle(frame, (10, 10), (220, 50), (15, 20, 32), -1)
        cv2.putText(frame, f"VEHICLES: {self.transit_count}", (20, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

def run_integrated_simulation():
    print("=========================================")
    print("Milestone 3: Dynamic Tracking Audit")
    print("=========================================")
    
    # 1. Create simulated traffic MP4 file
    temp_video = "temp_tracking_feed.avi"
    print("Generating simulated roadway video...")
    
    width, height = 640, 480
    line_y = 300
    
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_video, fourcc, 10.0, (width, height))
    for i in range(40):
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50
        car_y = 50 + i * 10
        cv2.rectangle(frame, (270, car_y - 30), (370, car_y + 30), (120, 120, 120), -1)
        cv2.circle(frame, (280, car_y + 30), 10, (10, 10, 10), -1)
        cv2.circle(frame, (360, car_y + 30), 10, (10, 10, 10), -1)
        out.write(frame)
    out.release()

    # 2. Instantiate and start resilient edge tracker
    tracker = ResilientEdgeTracker("CAM-GK-01", temp_video)
    tracker.start()

    # Give stream worker 1 second to start decoding
    time.sleep(1.0)

    # 3. Process frame sequence
    print("Processing active frames...")
    output_video_path = "integrated_tracking_output.avi"
    out_writer = cv2.VideoWriter(output_video_path, fourcc, 10.0, (width, height))

    for _ in range(40):
        processed = tracker.process_next_frame(line_y)
        if processed is not None:
            out_writer.write(processed)
        time.sleep(0.05)

    out_writer.release()
    tracker.stop()

    # Clean up local video file
    if os.path.exists(temp_video):
        os.remove(temp_video)

    print("=========================================")
    print("Verification and Simulation Complete.")
    print(f"Output video saved to: {output_video_path}")
    print(f"Total counted vehicles: {tracker.transit_count}")
    print("=========================================")

if __name__ == "__main__":
    run_integrated_simulation()
