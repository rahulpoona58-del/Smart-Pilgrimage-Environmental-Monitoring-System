import os
import cv2
import json
import time
import requests
import numpy as np
from datetime import datetime, timezone
from ultralytics import YOLO

class DroneVisualProcessor:
    """
    Cloud-based microservice for processing dynamic aerial drone feeds.
    Ingests live RTMP / SRT streams, detects waste hotspots and water body pollution,
    estimates crowd density indices, and projects visual pixels to physical GPS points.
    """
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1", model_path: str = "models/yolov8n-seg.pt"):
        self.api_url = api_base_url
        self.auth_token = os.getenv("SPEMS_DRONE_AUTH_TOKEN", "drone-cloud-key-999")
        
        # Load high-capacity segmenting YOLOv8 model for complex aerial layouts
        try:
            self.model = YOLO(model_path)
        except Exception:
            self.model = None
            print("[Warning] Deep segmentation model not found. Operating under layout fallback mode.")

        # In-memory registry storing active flight state parameters
        # Mapped: drone_uav_id -> dict of latest coordinates, altitude, gimbal angle
        self.drone_telemetries = {}

    def update_drone_telemetry(self, uav_id: str, lat: float, lng: float, altitude: float, heading: float):
        """Allows drone ground-stations to post real-time UAV flight telemetry coordinates."""
        self.drone_telemetries[uav_id] = {
            "latitude": lat,
            "longitude": lng,
            "altitude": altitude,
            "heading": heading,
            "last_updated": time.time()
        }
        print(f"[Telemetry Ingest] UAV {uav_id} telemetry registered: Lat={lat}, Lng={lng}, Alt={altitude}m")

    def project_pixel_to_gps(self, pixel_coords: tuple, frame_shape: tuple, drone_state: dict) -> tuple:
        """
        Georeferencing projection algorithm.
        Estimates the physical GPS coordinate of a detected object on the ground
        based on the drone's absolute position, height, heading, and pixel offset.
        """
        px, py = pixel_coords
        fh, fw = frame_shape[:2]
        
        # Absolute flight values
        d_lat = drone_state["latitude"]
        d_lng = drone_state["longitude"]
        alt = drone_state["altitude"]
        heading = drone_state["heading"] # Degree orientation relative to North (0-360)

        # Standard lens field of view (FOV) parameters (e.g. 84 degrees)
        fov_diagonal = 84.0
        aspect_ratio = fw / fh
        fov_horizontal = fov_diagonal * (aspect_ratio / np.sqrt(aspect_ratio**2 + 1))
        fov_vertical = fov_diagonal * (1 / np.sqrt(aspect_ratio**2 + 1))

        # Calculate offset percentages relative to the optical center
        dx_pct = (px - (fw / 2)) / (fw / 2)
        dy_pct = ((fh / 2) - py) / (fh / 2) # Inverse y-axis for physical ground offset

        # Estimate ground footprint dimensions (width & height of standard view patch)
        ground_half_width = alt * np.tan(np.radians(fov_horizontal / 2))
        ground_half_height = alt * np.tan(np.radians(fov_vertical / 2))

        # Compute ground physical offsets in meters
        offset_x_m = dx_pct * ground_half_width
        offset_y_m = dy_pct * ground_half_height

        # Rotate offsets based on the drone's true flight heading
        rad = np.radians(heading)
        rot_x_m = offset_x_m * np.cos(rad) - offset_y_m * np.sin(rad)
        rot_y_m = offset_x_m * np.sin(rad) + offset_y_m * np.cos(rad)

        # Approximate coordinate conversions (1 degree lat ~= 111,000m; 1 degree lng ~= 111,000 * cos(lat))
        delta_lat = rot_y_m / 111000.0
        delta_lng = rot_x_m / (111000.0 * np.cos(np.radians(d_lat)))

        projected_lat = d_lat + delta_lat
        projected_lng = d_lng + delta_lng

        return projected_lat, projected_lng

    def analyze_water_color_ph_plume(self, frame_patch: np.ndarray) -> tuple:
        """
        Heuristic segmentation detecting chemical or sediment waste plumes.
        Extracts color thresholds inside the HSV spectrum to isolate pollution plumes.
        Returns: matching segment area percentage and estimated severity.
        """
        # Convert crop patch to HSV color space
        hsv = cv2.cvtColor(frame_patch, cv2.COLOR_BGR2HSV)
        
        # Standard clean river color ranges (Ganges/Alaknanda blue-green shades)
        # Define ranges for "muddy/polluted/chemical" plume variations
        lower_plume = np.array([10, 30, 20])
        upper_plume = np.array([35, 255, 200])

        mask = cv2.inRange(hsv, lower_plume, upper_plume)
        plume_pixels = cv2.countNonZero(mask)
        total_pixels = frame_patch.shape[0] * frame_patch.shape[1]

        plume_ratio = plume_pixels / total_pixels
        severity = "Low"
        if plume_ratio > 0.40:
            severity = "High"
        elif plume_ratio > 0.15:
            severity = "Medium"

        return plume_ratio, severity

    def post_drone_violation(self, uav_id: str, v_type: str, severity: str, frame: np.ndarray, gps: tuple) -> bool:
        """Saves dynamic violation data and uploads visual keyframe to main API."""
        filename = f"drone_violation_{v_type.lower()}_{int(time.time())}.jpg"
        temp_path = f"/tmp/{filename}" if os.name != 'nt' else f"evidence/{filename}"
        
        # Ensure evidence folder exists
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        cv2.imwrite(temp_path, frame)

        timestamp_str = datetime.now(timezone.utc).isoformat() + "Z"
        
        payload = {
            "location_id": "1", # Gaurikund Base default for testing
            "camera_id": f"DRONE-{uav_id}",
            "plate_number": "",
            "violation_type": v_type,
            "severity_level": severity,
            "violation_timestamp": timestamp_str,
            "latitude": str(gps[0]),
            "longitude": str(gps[1])
        }

        try:
            files = {'evidence_image': (filename, open(temp_path, 'rb'), 'image/jpeg')}
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(f"{self.api_url}/violations", data=payload, files=files, headers=headers, timeout=10.0)
            if response.status_code == 201:
                print(f"[Drone Event Upload] Posted {v_type} event to cloud DB: Coordinates={gps}")
                return True
        except Exception as e:
            print(f"[Upload Error] Drone microservice failed to upload violation: {e}")
        return False

    def ingest_rtmp_stream(self, uav_id: str, stream_url: str):
        """
        Establishes connection to the drone's RTMP/SRT broadcast server using PyAV.
        Executes real-time decoding, crowd counts, and geolocates environmental infractions.
        """
        print(f"[Drone Video Ingest] Connecting to live UAV feed: {stream_url}...")
        
        try:
            import av
            container = av.open(stream_url)
            stream = container.streams.video[0]
        except Exception as e:
            print(f"[Ingest Error] Failed to open RTMP container: {e}. Running simulation fallback...")
            self.run_simulation_fallback(uav_id)
            return

        frame_count = 0
        for packet in container.demux(stream):
            for frame in packet.decode():
                frame_count += 1
                if frame_count % 30 != 0: # Process only 1 frame per second to optimize GPU loads
                    continue

                # Convert PyAV frame to standard OpenCV numpy array
                img = frame.to_ndarray(format='bgr24')
                fh, fw = img.shape[:2]

                # Fetch matching flight telemetry parameters
                drone_state = self.drone_telemetries.get(uav_id, {
                    "latitude": 30.6502,
                    "longitude": 79.0053,
                    "altitude": 120.0,
                    "heading": 180.0
                })

                # Default variables
                people_count = 0
                waste_hotspots = []

                # Run segmentation inference if active YOLOv8 model weights are loaded
                if self.model:
                    results = self.model(img, verbose=False)
                    if results and len(results[0].boxes) > 0:
                        boxes = results[0].boxes
                        for box in boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            
                            # Standard COCO class mappings: 0 (person), 39 (bottle), 41 (cup), 62 (trash)
                            if cls_id == 0:
                                people_count += 1
                            elif cls_id in [39, 41, 62] and conf > 0.40:
                                coords = box.xyxy[0].cpu().numpy()
                                px = int((coords[0] + coords[2]) / 2)
                                py = int((coords[1] + coords[3]) / 2)
                                waste_hotspots.append((px, py))

                # 1. EVALUATE CROWD DENSITY
                if people_count > 50:
                    # High density alert (>50 people visible in small grid area)
                    center_px = (fw // 2, fh // 2)
                    gps_loc = self.project_pixel_to_gps(center_px, img.shape, drone_state)
                    print(f"[Crowd Density Alert] Overhead overcrowding index high! Count: {people_count}")
                    self.post_drone_violation(uav_id, "Overcrowding", "Medium", img, gps_loc)

                # 2. EVALUATE ILLEGAL DUMPING / WASTE PILES
                if len(waste_hotspots) >= 8:
                    # Dense cluster of garbage boxes marks an illegal dumping hotspot
                    avg_px = int(np.mean([pt[0] for pt in waste_hotspots]))
                    avg_py = int(np.mean([pt[1] for pt in waste_hotspots]))
                    gps_loc = self.project_pixel_to_gps((avg_px, avg_py), img.shape, drone_state)
                    print(f"[Dumping Alert] Found solid waste accumulation hotspot at coordinates: {gps_loc}")
                    self.post_drone_violation(uav_id, "Illegal_Dumping", "High", img, gps_loc)

                # 3. EVALUATE RIVER POLLUTION PLUMES
                # Focus check on the lower center quadrant (typical location of rivers in valley flight paths)
                river_patch = img[int(fh*0.6):int(fh*0.9), int(fw*0.3):int(fw*0.7)]
                plume_ratio, severity = self.analyze_water_color_ph_plume(river_patch)
                if plume_ratio > 0.15:
                    plume_center = (fw // 2, int(fh * 0.75))
                    gps_loc = self.project_pixel_to_gps(plume_center, img.shape, drone_state)
                    print(f"[Water Quality Alert] Found water quality plume anomaly (ratio={plume_ratio:.2f})!")
                    self.post_drone_violation(uav_id, "River_Pollution", severity, img, gps_loc)

    def run_simulation_fallback(self, uav_id: str):
        """Simulation testing fallback, executing mock surveillance pipelines in sandbox contexts."""
        print(f"[Simulation Fallback] Starting telemetry mock flight path loop for UAV {uav_id}...")
        
        # Simulate a flight route over Kedarnath Gaurikund base
        lat_start, lng_start = 30.6500, 79.0050
        
        for step in range(10):
            # Advance coordinates along linear flight vector
            lat = lat_start + step * 0.0001
            lng = lng_start + step * 0.0001
            
            # Post flight coordinates parameters
            self.update_drone_telemetry(uav_id, lat, lng, altitude=80.0, heading=45.0)
            
            # Simulate a river pollution flag on step 3
            if step == 3:
                mock_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                # Paint mock yellow-brown water sediment chemical pattern
                cv2.circle(mock_frame, (640, 360), 200, (20, 100, 120), -1)
                
                # Project coordinates
                gps = (lat + 0.00005, lng + 0.00005)
                self.post_drone_violation(uav_id, "River_Pollution", "High", mock_frame, gps)
                
            time.sleep(2.0)

if __name__ == "__main__":
    processor = DroneVisualProcessor(api_base_url="http://localhost:8000/api/v1")
    # Spin drone processing pipeline on separate thread to allow concurrent operations
    processor.run_simulation_fallback("UAV-CHAR-DHAM-01")
