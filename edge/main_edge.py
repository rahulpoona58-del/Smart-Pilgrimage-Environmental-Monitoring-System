import os
import cv2
import yaml
import time
import requests
import threading
import numpy as np
import logging
from datetime import datetime, timezone

from cv_pipelines.vehicle_tracker import VehicleTracker
from cv_pipelines.anpr_engine import ANPREngine
from cv_pipelines.zone_monitor import ZoneMonitor
from cv_pipelines.dumping_detector import DumpingDetector
from utils.failsafe_buffer import FailsafeBuffer
from utils.camera_ingest import MultiCameraIngestManager
from utils.logging_config import setup_edge_logging

# Configure logging for Edge node
setup_edge_logging()
logger = logging.getLogger("spems.edge.supervisor")

class EdgeSupervisor:
    """
    Coordinates real-time operations across multiple cameras at an Edge Node.
    Loads configurations, handles video decoding, tracks vehicle coordinates,
    extracts license plates, evaluates geofence boundaries, and pushes outputs to cloud APIs.
    """
    def __init__(self, config_path: str = "config.yaml"):
        # Load local configuration rules
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.node_id = self.config["edge_node_id"]
        self.location_id = self.config["location_id"]
        self.api_url = self.config["cloud"]["api_base_url"]
        self.auth_token = self.config["cloud"]["auth_token"]

        # Initialize engines
        self.tracker = VehicleTracker()
        self.anpr = ANPREngine()
        self.buffer = FailsafeBuffer()
        
        # Initialize spatial and dumping monitors
        self.zone_monitor = ZoneMonitor()
        self.dumping_detector = DumpingDetector()

        # Unified Multi-Threaded Camera Ingest Manager
        self.ingest_manager = MultiCameraIngestManager()

        # In-memory registry to prevent double-logging plates in the same session
        # Maps track_id -> Plate string details to handle tracking drift
        self.active_tracks = {}
        self.track_ocr_history = {} # Maps track_id -> list of (plate_text, confidence)

        self.network_active = True
        self.shutdown_flag = threading.Event()

    def check_network_connectivity(self) -> bool:
        """Pings central API to assess connectivity state."""
        try:
            # Quick lightweight health check request
            response = requests.get(f"{self.api_url}/health", timeout=3.0)
            self.network_active = response.status_code == 200
        except requests.RequestException:
            self.network_active = False
        return self.network_active

    def upload_vehicle_log(self, plate: str, camera_id: str, log_type: str, confidence: float) -> bool:
        """Pushes a vehicle transit log payload to cloud API, falling back to SQLite buffer if offline."""
        timestamp_str = datetime.now(timezone.utc).isoformat() + "Z"
        payload = {
            "plate_number": plate,
            "camera_id": camera_id,
            "location_id": self.location_id,
            "log_type": log_type,
            "timestamp": timestamp_str,
            "raw_confidence": confidence
        }

        if not self.network_active:
            self.buffer.buffer_vehicle_log(plate, camera_id, self.location_id, log_type, timestamp_str, confidence)
            return False

        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(f"{self.api_url}/logs/vehicle", json=payload, headers=headers, timeout=5.0)
            if response.status_code == 201:
                return True
        except requests.RequestException:
            pass

        # If call fails, cache in SQLite buffer
        self.buffer.buffer_vehicle_log(plate, camera_id, self.location_id, log_type, timestamp_str, confidence)
        return False

    def upload_violation(self, camera_id: str, plate: str, v_type: str, severity: str, frame: np.ndarray, coords: tuple) -> bool:
        """Pushes an environmental infraction event and evidence image to the cloud endpoint."""
        timestamp_str = datetime.now(timezone.utc).isoformat() + "Z"
        
        # Save frame locally as evidence WebP file for bandwidth optimization
        filename = f"evidence_{v_type.lower()}_{int(time.time())}.webp"
        evidence_dir = "evidence/violations"
        os.makedirs(evidence_dir, exist_ok=True)
        img_path = os.path.join(evidence_dir, filename)
        cv2.imwrite(img_path, frame, [cv2.IMWRITE_WEBP_QUALITY, 75])

        if not self.network_active:
            self.buffer.buffer_violation(self.location_id, camera_id, plate, v_type, severity, img_path, coords, timestamp_str)
            return False

        # In production, this would perform a multipart file post to an S3-enabled API Gateway
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            files = {'evidence_image': (filename, open(img_path, 'rb'), 'image/webp')}
            payload = {
                "location_id": str(self.location_id),
                "camera_id": camera_id,
                "plate_number": plate if plate else "",
                "violation_type": v_type,
                "severity_level": severity,
                "violation_timestamp": timestamp_str,
                "latitude": str(coords[0]),
                "longitude": str(coords[1])
            }
            response = requests.post(f"{self.api_url}/violations", data=payload, files=files, headers=headers, timeout=10.0)
            if response.status_code == 201:
                return True
        except requests.RequestException as e:
            logger.error(f"[Upload Error] Connection failed: {e}")

        # If network call fails, save to SQLite buffer
        self.buffer.buffer_violation(self.location_id, camera_id, plate, v_type, severity, img_path, coords, timestamp_str)
        return False

    def buffer_synchronization_loop(self):
        """Background thread that continuously checks network state and synchronizes buffered local SQLite queues."""
        logger.info("[Buffer Sync] Initializing offline storage synchronization scheduler...")
        while not self.shutdown_flag.is_set():
            if self.check_network_connectivity():
                # 1. Sync vehicle transit logs
                logs = self.buffer.fetch_all_buffered_logs()
                if logs:
                    logger.info(f"[Buffer Sync] Connecting online: uploading {len(logs)} buffered vehicle logs...")
                    successful_ids = []
                    for log in logs:
                        # Attempt to post log
                        payload = {
                            "plate_number": log["plate_number"],
                            "camera_id": log["camera_id"],
                            "location_id": log["location_id"],
                            "log_type": log["log_type"],
                            "timestamp": log["timestamp"],
                            "raw_confidence": log["raw_confidence"]
                        }
                        try:
                            headers = {"Authorization": f"Bearer {self.auth_token}"}
                            response = requests.post(f"{self.api_url}/logs/vehicle", json=payload, headers=headers, timeout=5.0)
                            if response.status_code == 201:
                                successful_ids.append(log["id"])
                        except requests.RequestException:
                            break # Network interrupted again, abort sync iteration
                    
                    if successful_ids:
                        self.buffer.remove_buffered_logs(successful_ids)
                        logger.info(f"[Buffer Sync] Purged {len(successful_ids)} uploaded records from local database.")

                # 2. Sync violation events
                violations = self.buffer.fetch_all_buffered_violations()
                if violations:
                    logger.info(f"[Buffer Sync] Inbound connection active: uploading {len(violations)} cached violations...")
                    successful_ids = []
                    for v in violations:
                        try:
                            # Re-verify local evidence file exists
                            if not os.path.exists(v["evidence_image_path"]):
                                # If image is lost, dismiss violation from cache to prevent infinite loops
                                successful_ids.append(v["id"])
                                continue
                                
                            filename = os.path.basename(v["evidence_image_path"])
                            files = {'evidence_image': (filename, open(v["evidence_image_path"], 'rb'), 'image/webp')}
                            
                            import json
                            gps = json.loads(v["violation_coordinates"])
                            
                            payload = {
                                "location_id": str(v["location_id"]),
                                "camera_id": v["camera_id"],
                                "plate_number": v["plate_number"] if v["plate_number"] else "",
                                "violation_type": v["violation_type"],
                                "severity_level": v["severity_level"],
                                "violation_timestamp": v["violation_timestamp"],
                                "latitude": str(gps["lat"]),
                                "longitude": str(gps["lng"])
                            }
                            headers = {"Authorization": f"Bearer {self.auth_token}"}
                            response = requests.post(f"{self.api_url}/violations", data=payload, files=files, headers=headers, timeout=10.0)
                            if response.status_code == 201:
                                successful_ids.append(v["id"])
                        except requests.RequestException:
                            break # Connection dropped again, stop synchronization
                    
                    if successful_ids:
                        self.buffer.remove_buffered_violations(successful_ids)
                        logger.info(f"[Buffer Sync] Synchronized {len(successful_ids)} violations, local cache refreshed.")
            
            # Wait 10 seconds between offline synchronization sweeps
            self.shutdown_flag.wait(10.0)

    def process_camera_stream(self, cam_config: dict):
        """Individual camera thread processing RTSP loops and routing video frames through YOLO models."""
        camera_id = cam_config["id"]
        stream_url = cam_config["url"]
        anpr_enabled = cam_config["anpr_enabled"]
        litter_enabled = cam_config["litter_enabled"]
        roi_poly = cam_config.get("roi_polygon", [])
        restricted_zones = cam_config.get("restricted_zones", [])
        no_parking_zones = cam_config.get("no_parking_zones", [])
        river_zones = cam_config.get("river_zones", [])
        designated_bin_zones = cam_config.get("designated_bin_zones", [])
        
        # Camera physical georeference placement for geotag calculation
        lat = cam_config.get("latitude", 30.6500)
        lng = cam_config.get("longitude", 79.0050)

        logger.info(f"[Stream Worker] Starting processing thread for: {camera_id} via RTSP {stream_url}")
        
        # Ingest manager tracks and connects streams; we fetch frames asynchronously
        frame_counter = 0

        while not self.shutdown_flag.is_set():
            frame = self.ingest_manager.fetch_frame(camera_id)
            if frame is None:
                # Sleep briefly to avoid high CPU spin-lock polling
                time.sleep(0.01)
                continue

            frame_counter += 1
            # Skip frames to manage edge processor load (configurable via frame_skip)
            if frame_counter % self.config["inference"]["frame_skip"] != 0:
                continue

            # 1. Run Object Detection & ByteTrack tracking for vehicles
            tracked_vehicles = self.tracker.detect_and_track(frame)

            for vehicle in tracked_vehicles:
                x1, y1, x2, y2 = vehicle["bbox"]
                track_id = vehicle["track_id"]
                class_name = vehicle["class_name"]
                conf = vehicle["confidence"]

                # A. ANPR Engine Execution with Multi-Frame Consensus Voting
                if anpr_enabled and track_id not in self.active_tracks:
                    vehicle_crop = frame[y1:y2, x1:x2]
                    plate_text, ocr_conf, plate_crop = self.anpr.extract_plate(vehicle_crop)
                    
                    if plate_text and ocr_conf > 0.40:
                        # Append to history
                        if track_id not in self.track_ocr_history:
                            self.track_ocr_history[track_id] = []
                        self.track_ocr_history[track_id].append((plate_text, ocr_conf))
                        
                        # Once we collect 3 samples or if confidence is extremely high (e.g. >0.92)
                        history = self.track_ocr_history[track_id]
                        if len(history) >= 3 or ocr_conf > 0.92:
                            # Standard majority vote
                            plate_counts = {}
                            for p, c in history:
                                plate_counts[p] = plate_counts.get(p, 0) + 1
                            
                            best_plate = max(plate_counts, key=plate_counts.get)
                            conf_sum = sum(c for p, c in history if p == best_plate)
                            conf_count = sum(1 for p, c in history if p == best_plate)
                            avg_conf = conf_sum / conf_count
                            
                            self.active_tracks[track_id] = best_plate
                            logger.info(f"[ANPR Consensus Trigger] Found License Plate: {best_plate} (Avg Conf: {avg_conf:.2f}, Samples: {len(history)}) on track {track_id}")
                            
                            # Upload log (Assumed entry direction at gate)
                            threading.Thread(
                                target=self.upload_vehicle_log, 
                                args=(best_plate, camera_id, "ENTRY", avg_conf),
                                daemon=True
                            ).start()

                # Get registered plate number for this vehicle if available
                plate_no = self.active_tracks.get(track_id, None)

                # B. Run Spatial Rules Check (Restricted-Area, Illegal Parking, Wrong-Way Routing)
                v_spatial = self.zone_monitor.evaluate_vehicle_rules(
                    track_id=track_id,
                    bbox=(x1, y1, x2, y2),
                    class_name=class_name,
                    no_parking_zones=no_parking_zones,
                    restricted_zones=restricted_zones,
                    allowed_direction_vector=cam_config.get("allowed_direction_vector", (0, 1))
                )

                if v_spatial:
                    threading.Thread(
                        target=self.upload_violation,
                        args=(
                            camera_id, 
                            plate_no, 
                            v_spatial["violation_type"], 
                            v_spatial["severity_level"], 
                            frame, 
                            (lat, lng)
                        ),
                        daemon=True
                    ).start()

            # 2. Run Litter and Dumping Detection (Milestones 8 & 9)
            if litter_enabled:
                detected_waste = []
                # Use loaded model to track COCO class 39 ('bottle' representing general litter/plastics)
                results_waste = self.tracker.model.track(
                    source=frame,
                    conf=0.25,
                    classes=[39], # 'bottle'
                    persist=True,
                    verbose=False
                )
                if results_waste and len(results_waste) > 0:
                    for box in results_waste[0].boxes:
                        if box.id is not None:
                             w_track_id = int(box.id[0].item())
                             w_coords = box.xyxy[0].cpu().numpy()
                             wx1, wy1, wx2, wy2 = map(int, w_coords)
                             detected_waste.append({
                                 "track_id": w_track_id,
                                 "bbox": (wx1, wy1, wx2, wy2),
                                 "class_name": "bottle"
                             })

                if detected_waste:
                    violations = self.dumping_detector.analyze_waste(
                        detected_waste=detected_waste,
                        frame=frame,
                        river_zones=river_zones,
                        designated_bin_zones=designated_bin_zones,
                        camera_coords=(lat, lng)
                    )
                    for v in violations:
                        threading.Thread(
                            target=self.upload_violation,
                            args=(
                                camera_id, 
                                v["associated_plate"], 
                                v["violation_type"], 
                                v["severity_level"], 
                                v["evidence_frame"], 
                                v["geotag"]
                            ),
                            daemon=True
                        ).start()

    def execute(self):
        """Initializes processing threads for all camera feeds and starts the database synchronization task."""
        # 1. Start the Background Offline Synchronization loop
        sync_thread = threading.Thread(target=self.buffer_synchronization_loop, daemon=True)
        sync_thread.start()

        # 2. Register all cameras in the unified ingest manager first
        for cam_config in self.config["cameras"]:
            self.ingest_manager.register_camera(cam_config["id"], cam_config["url"])

        # 3. Spin up concurrent background thread workers for frame capture
        self.ingest_manager.start_all_streams()

        # 4. Start independent processing threads for each camera RTSP configuration
        camera_threads = []
        for cam_config in self.config["cameras"]:
            t = threading.Thread(target=self.process_camera_stream, args=(cam_config,), daemon=True)
            t.start()
            camera_threads.append(t)

        logger.info(f"[Supervisor] Edge Processing node initialized. Running {len(camera_threads)} active camera pipelines.")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            logger.info("[Supervisor] Received shutdown command. Stopping camera threads...")
            self.shutdown_flag.set()
            self.ingest_manager.stop_all_streams()
            sync_thread.join(timeout=2.0)

if __name__ == "__main__":
    supervisor = EdgeSupervisor("config.yaml")
    supervisor.execute()
