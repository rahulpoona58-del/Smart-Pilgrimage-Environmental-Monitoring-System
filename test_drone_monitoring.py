# test_drone_monitoring.py
# Verification Test Harness for Milestone 12: Drone Monitoring and Aerial Analytics Engine.

import cv2
import numpy as np
import time
import os
import requests
import sys
from datetime import datetime, timezone

# Prevent Unicode encoding issues in Windows command prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Import modular drone visual processor components
from ai_services.drone_processor.main import DroneVisualProcessor

class DroneTestOrchestrator:
    """
    Orchestrates the drone aerial surveillance pipeline mock flight.
    Feeds simulated telemetry vectors and frames to the DroneVisualProcessor,
    projects visual anomalies to physical coordinates, and pushes tickets to the FastAPI DB.
    """
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
        self.uav_id = "UAV-PATROL-MANDAKINI"
        self.processor = DroneVisualProcessor(api_base_url=self.api_url)
        
        # Ground truth flight coordinates (Starts at Gaurikund Base, moves East)
        self.lat_start = 30.6502
        self.lng_start = 79.0053
        self.altitude = 90.0 # meters
        self.heading = 90.0 # heading East

    def run_surveillance_flight(self):
        print("=========================================")
        print("Drone Aerial Surveillance Flight Simulation")
        print("=========================================")

        # Quick online check before initiating API request loops
        try:
            health = requests.get(f"{self.api_url.replace('/api/v1', '')}/health", timeout=3.0)
            if health.status_code == 200:
                print("[Status OK] Central FastAPI backend is active and reachable.")
            else:
                print(f"[Status Error] Received unexpected status code: {health.status_code}")
                return
        except requests.RequestException:
            print("[Status Error] Central FastAPI backend offline. Skip live API dispatch.")
            return

        # Create virtual canvas representing drone camera (width: 1280, height: 720)
        width, height = 1280, 720

        # Step 1: Telemetry Ingestion (Post UAV current coordinates)
        print("\nStep 1: Registering UAV Telemetry Vector...")
        self.processor.update_drone_telemetry(
            uav_id=self.uav_id,
            lat=self.lat_start,
            lng=self.lng_start,
            altitude=self.altitude,
            heading=self.heading
        )

        # Step 2: Simulate Aerial River Pollution (HSV color Plume anomaly)
        print("\nStep 2: Simulating River Plume Sediment Contamination Frame...")
        frame_plume = np.ones((height, width, 3), dtype=np.uint8) * 110 # Deep clean river blue-green
        # Paint muddy sediment plume pattern (brown-yellow hue) in the bottom-center region of lens
        cv2.circle(frame_plume, (640, 540), 180, (28, 90, 110), -1) 
        cv2.putText(frame_plume, "UAV CAMERA 4K - MANDAKINI CHANNEL", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.rectangle(frame_plume, (384, 432), (896, 648), (0, 0, 255), 2) # Highlight target checking box

        # Run Plume Analysis
        river_patch = frame_plume[432:648, 384:896]
        plume_ratio, severity = self.processor.analyze_water_color_ph_plume(river_patch)
        print(f"[Heuristic Result] Plume Ratio Detected: {plume_ratio:.2%}, Priority: {severity}")

        if plume_ratio > 0.15:
            # Georeference: Project optical center of pollution plume to physical GPS
            plume_center = (640, 540)
            drone_state = self.processor.drone_telemetries[self.uav_id]
            projected_gps = self.processor.project_pixel_to_gps(plume_center, frame_plume.shape, drone_state)
            print(f"[Georeferencing] Projected anomaly to absolute GPS: Lat={projected_gps[0]:.6f}, Lng={projected_gps[1]:.6f}")

            # Upload ticket to central DB
            success = self.processor.post_drone_violation(
                uav_id=self.uav_id,
                v_type="River_Pollution",
                severity=severity,
                frame=frame_plume,
                gps=projected_gps
            )
            if success:
                print("[Verification Success] Georeferenced River Pollution ticket created in database.")

        # Step 3: Simulate Dynamic Overcrowding / Crowd Density
        print("\nStep 3: Simulating Pilgrims Crowd Density Anomaly...")
        frame_crowd = np.ones((height, width, 3), dtype=np.uint8) * 60 # Dark gray asphalt background
        cv2.putText(frame_crowd, "UAV CAMERA 4K - SHIRK ROAD AREA", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Mock 60 pilgrim coordinates in the optical frame representing high-density congestion
        mock_pilgrims_count = 64
        for idx in range(mock_pilgrims_count):
            rx = int(320 + (idx % 8) * 80 + np.random.randint(-15, 15))
            ry = int(180 + (idx // 8) * 60 + np.random.randint(-15, 15))
            cv2.rectangle(frame_crowd, (rx - 10, ry - 20), (rx + 10, ry + 20), (0, 255, 0), 1) # Pilgrim bounding box representation

        print(f"[Simulation Crowd Engine] Visible Overhead Crowd Count: {mock_pilgrims_count} pilgrims")
        if mock_pilgrims_count > 50:
            center_px = (640, 360)
            drone_state = self.processor.drone_telemetries[self.uav_id]
            projected_gps = self.processor.project_pixel_to_gps(center_px, frame_crowd.shape, drone_state)
            print(f"[Georeferencing] Projected crowd center coordinates: Lat={projected_gps[0]:.6f}, Lng={projected_gps[1]:.6f}")

            # Upload overcrowding ticket
            success = self.processor.post_drone_violation(
                uav_id=self.uav_id,
                v_type="Overcrowding",
                severity="Medium",
                frame=frame_crowd,
                gps=projected_gps
            )
            if success:
                print("[Verification Success] Geolocated Overcrowding ticket created in database.")

        print("\n=========================================")
        print("Drone Aerial Flight Simulation Completed.")
        print("=========================================")

if __name__ == "__main__":
    orchestrator = DroneTestOrchestrator()
    orchestrator.run_surveillance_flight()
