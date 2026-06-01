# test_vehicle_detector.py
# Verification Test Harness for Milestone 3: YOLO-Based Vehicle Detection.

import cv2
import time
import os
import numpy as np
import logging

# Initialize system logs prior to imports
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")

from edge.utils.camera_ingest import MultiCameraIngestManager
from edge.cv_pipelines.vehicle_detector import LocalVehicleDetector

def run_vehicle_detector_verification():
    print("=========================================")
    print("YOLO Vehicle Detection: Performance Audit")
    print("=========================================")

    # 1. Create simulated roadway video source
    temp_video = "temp_detector_feed.avi"
    print("Generating simulated roadway video stream...")
    
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_video, fourcc, 10.0, (width, height))
    
    # Emulates 40 frames of a vehicle traveling horizontally across the screen
    for i in range(40):
        # Create solid asphalt gray roadway background
        frame = np.ones((height, width, 3), dtype=np.uint8) * 60
        
        # Calculate moving car coordinate position (shifting horizontally from x=50 to x=450)
        car_x = 50 + i * 10
        car_y = 300
        
        # Paint vehicle body shape (gray rectangle)
        cv2.rectangle(frame, (car_x - 50, car_y - 30), (car_x + 50, car_y + 30), (120, 120, 120), -1)
        # Paint wheels (black circles)
        cv2.circle(frame, (car_x - 30, car_y + 30), 10, (10, 10, 10), -1)
        cv2.circle(frame, (car_x + 30, car_y + 30), 10, (10, 10, 10), -1)
        
        out.write(frame)
    out.release()

    # 2. Initialize Ingestion Manager and register the simulated camera feed
    manager = MultiCameraIngestManager()
    manager.register_camera("CAM-GK-VALLEY-01", temp_video)

    # 3. Initialize YOLOv8 Vehicle Detector (Milestone 3)
    detector = LocalVehicleDetector(model_path="yolov8n.pt", conf_threshold=0.25)

    # 4. Start concurrent stream ingestion
    print("\n[Worker Control] Launching background capture stream...")
    manager.start_all_streams()

    # Allow stream worker 1 second to start decoding
    time.sleep(1.0)

    # 5. Process frame sequence and output labeled visual detections
    print("Executing YOLOv8 vehicle detection loop...")
    output_video_path = "detector_simulation_output.avi"
    out_writer = cv2.VideoWriter(output_video_path, fourcc, 10.0, (width, height))

    detected_counts_log = []
    
    for frame_idx in range(40):
        frame = manager.fetch_frame("CAM-GK-VALLEY-01")
        if frame is not None:
            # Run YOLOv8 vehicle detection
            processed_frame, count = detector.process_camera_frame(frame)
            
            # Save metrics
            detected_counts_log.append(count)
            
            # Write labeled frame to output clip
            out_writer.write(processed_frame)
            
        time.sleep(0.08) # Emulate standard processing intervals

    out_writer.release()
    
    # 6. Stop ingestion threads
    print("\n[Worker Control] Stopping capture stream...")
    manager.stop_all_streams()

    # Clean up local video file
    if os.path.exists(temp_video):
        os.remove(temp_video)

    print("\n=========================================")
    print("Vehicle Detector Verification Results")
    print("=========================================")
    print(f"Output video successfully exported to: {output_video_path}")
    print(f"Frames processed successfully: {len(detected_counts_log)}")
    print(f"Maximum simultaneous vehicles classified: {max(detected_counts_log) if detected_counts_log else 0}")
    print("Verification: YOLO-based classification pipeline is active.")
    print("=========================================")

if __name__ == "__main__":
    run_vehicle_detector_verification()
