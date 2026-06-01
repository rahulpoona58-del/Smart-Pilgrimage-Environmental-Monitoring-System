# test_camera_ingest.py
# Verification Test Harness for Milestone 2: CCTV Ingestion System.

import cv2
import time
import os
import sys
import numpy as np
import logging

# Prevent Unicode encoding issues in Windows command prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Bootstrap system logs prior to imports
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")

from edge.utils.camera_ingest import MultiCameraIngestManager

def run_ingest_verification_test():
    print("=========================================")
    print("CCTV Ingestion System: Performance Audit")
    print("=========================================")

    # 1. Create a local temporary MP4 test file to represent a camera source
    # Emulates a 5-second video clip using blank frames painted with time markers
    temp_video = "temp_ingest_feed.avi"
    print("Generating simulated video source stream...")
    
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_video, fourcc, 10.0, (640, 480))
    for i in range(50): # 50 frames @ 10fps = 5 seconds
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, f"CAM-TEST FRAME {i}", (150, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        out.write(frame)
    out.release()

    # 2. Instantiate the multi-threaded Ingest Manager
    manager = MultiCameraIngestManager()

    # 3. Register cameras (Camera 1: local simulated MP4, Camera 2: invalid RTSP URL to test error recovery!)
    manager.register_camera("CAM-GK-01", temp_video)
    manager.register_camera("CAM-BD-OFFLINE-02", "rtsp://invalid-ip-mock:8554/live") # Offline network simulator

    # 4. Start all stream threads concurrently
    print("\n[Worker Control] Starting background capture threads...")
    manager.start_all_streams()

    # Let the threads ingest frames for 4 seconds
    print("Decoding frames in background. Auditing metrics...")
    time.sleep(4.0)

    # 5. Retrieve dynamic performance metrics
    metrics = manager.get_ingest_metrics()
    print("\n=========================================")
    print("Live Ingestion Metrics Reports")
    print("=========================================")
    for cid, m in metrics.items():
        print(f"Camera ID: {cid}")
        print(f"    Connection State: {'ONLINE' if m['is_connected'] else 'OFFLINE (Recovering...)'}")
        print(f"    Measured Ingestion FPS: {m['fps']}")
        print(f"    Total Frames Decoded: {m['total_decoded_frames']}")
        print(f"    Dropped Buffer Frames: {m['dropped_frames']}")
        print("-----------------------------------------")

    # 6. Verify single frame extraction capabilities
    frame = manager.fetch_frame("CAM-GK-01")
    if frame is not None:
        print(f"[Verification Success] Extracted frame size: {frame.shape}")
        # Save keyframe image to disk
        cv2.imwrite("extracted_ingest_keyframe.jpg", frame)
        print("Saved extracted keyframe: extracted_ingest_keyframe.jpg")
    else:
        print("[Verification Error] Failed to extract latest frame from buffer.")

    # 7. Gracefully stop all streams
    print("\n[Worker Control] Stopping capture threads...")
    manager.stop_all_streams()

    # Clean up local video file
    if os.path.exists(temp_video):
        os.remove(temp_video)

    print("=========================================")
    print("Ingestion System Verification Complete.")
    print("=========================================")

if __name__ == "__main__":
    run_ingest_verification_test()
