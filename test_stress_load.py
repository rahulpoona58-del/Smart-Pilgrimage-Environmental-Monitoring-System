# test_stress_load.py
# Production Load & Stress Testing Simulator: Simulates dynamic peak traffic workloads.

import time
import random
import threading
import requests
from datetime import datetime

API_BASE_URL = "http://localhost:8001/api/v1"

class LoadTestingSimulator:
    """
    Stress test simulator simulating high-frequency concurrent traffic transits,
    IoT sensor telemetries, and geolocated violations across multiple cameras.
    """
    def __init__(self, camera_count: int = 100, duration_seconds: int = 10):
        self.camera_count = camera_count
        self.duration_seconds = duration_seconds
        self.total_requests_attempted = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.stats_lock = threading.Lock()
        
        self.shutdown_flag = threading.Event()

    def simulate_camera_stream(self, camera_index: int):
        """Simulates a single camera stream posting telemetry and transit logs periodically."""
        camera_id = f"CAM-GK-STRESS-{camera_index:03d}"
        location_id = 1
        
        while not self.shutdown_flag.is_set():
            # 1. Simulate Vehicle Transit Log (ENTRY)
            plate_number = f"UK07TA{random.randint(1000, 9999)}"
            transit_payload = {
                "plate_number": plate_number,
                "camera_id": camera_id,
                "location_id": location_id,
                "log_type": "ENTRY",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "raw_confidence": round(random.uniform(0.75, 0.99), 2)
            }
            
            self.post_api_request(f"{API_BASE_URL}/logs/vehicle", transit_payload)

            # 2. Simulate High-Frequency Environmental Telemetry
            telemetry_payload = {
                "location_id": location_id,
                "device_id": f"IOT-STRESS-{camera_index:03d}",
                "pm25": round(random.uniform(10.0, 85.0), 1),
                "pm10": round(random.uniform(15.0, 110.0), 1),
                "aqi": int(random.uniform(20, 150)),
                "temperature": round(random.uniform(5.0, 28.0), 1),
                "humidity": round(random.uniform(30.0, 95.0), 1),
                "co2": round(random.uniform(350.0, 600.0), 1),
                "water_ph": round(random.uniform(6.8, 8.2), 1),
                "measured_at": datetime.utcnow().isoformat() + "Z"
            }
            self.post_api_request(f"{API_BASE_URL}/telemetry", telemetry_payload)

            # 3. Occasional environmental infraction (5% probability)
            if random.random() < 0.05:
                # Use a unique mock visual payload for testing
                violation_payload = {
                    "location_id": str(location_id),
                    "camera_id": camera_id,
                    "plate_number": plate_number,
                    "violation_type": "Littering",
                    "severity_level": "Medium",
                    "violation_timestamp": datetime.utcnow().isoformat() + "Z",
                    "latitude": f"{30.6500 + random.uniform(-0.005, 0.005):.6f}",
                    "longitude": f"{79.0050 + random.uniform(-0.005, 0.005):.6f}"
                }
                self.post_violation_request(violation_payload)

            # Control pacing to match target scale simulation
            time.sleep(random.uniform(1.0, 3.0))

    def post_api_request(self, url: str, payload: dict):
        """Executes REST POST request with telemetry collection."""
        with self.stats_lock:
            self.total_requests_attempted += 1
        try:
            res = requests.post(url, json=payload, timeout=3.0)
            with self.stats_lock:
                if res.status_code == 201:
                    self.successful_requests += 1
                else:
                    self.failed_requests += 1
        except requests.RequestException:
            with self.stats_lock:
                self.failed_requests += 1

    def post_violation_request(self, payload: dict):
        """Executes multipart violation post with unique mock image file bytes."""
        with self.stats_lock:
            self.total_requests_attempted += 1
        
        # Append dynamic bytes to prevent database anti-duplicate visual hash match failure
        evidence_bytes = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00' + bytes(random.randint(0, 255) for _ in range(16))
        
        try:
            files = {"evidence_image": ("stress_evidence.jpg", evidence_bytes, "image/jpeg")}
            res = requests.post(f"{API_BASE_URL}/violations", data=payload, files=files, timeout=3.0)
            with self.stats_lock:
                if res.status_code == 201:
                    self.successful_requests += 1
                else:
                    self.failed_requests += 1
        except requests.RequestException:
            with self.stats_lock:
                self.failed_requests += 1

    def run_stress_test(self):
        print("=========================================")
        print(f"SPEMS Production Stress Tester: {self.camera_count} Cameras")
        print("=========================================")
        print(f"Targeting: {API_BASE_URL}")
        print(f"Spawning {self.camera_count} simulated camera threads...")

        threads = []
        for i in range(self.camera_count):
            t = threading.Thread(target=self.simulate_camera_stream, args=(i,), daemon=True)
            threads.append(t)
            t.start()

        print("Threads running. Simulating traffic peaks...")
        time.sleep(self.duration_seconds)
        
        print("Stopping stress testing simulation...")
        self.shutdown_flag.set()
        
        print("\n=========================================")
        print("Stress Test Performance Summary Report")
        print("=========================================")
        print(f"Total Requests Dispatched : {self.total_requests_attempted}")
        print(f"Successful Requests (201) : {self.successful_requests}")
        print(f"Failed / Dropped Requests  : {self.failed_requests}")
        success_rate = (self.successful_requests / self.total_requests_attempted * 100) if self.total_requests_attempted > 0 else 0
        print(f"Transaction Success Rate  : {success_rate:.2f}%")
        print("=========================================")

if __name__ == "__main__":
    # Rapid sandbox verification limit: 50 cameras, 5 seconds to prevent thread pool lock on single laptop
    simulator = LoadTestingSimulator(camera_count=50, duration_seconds=5)
    simulator.run_stress_test()
