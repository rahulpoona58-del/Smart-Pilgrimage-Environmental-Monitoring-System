# edge/cv_pipelines/zone_monitor.py
# Milestone 7: Geofenced Zone Monitor and Violation Rules Engine.

import cv2
import numpy as np
import time
import logging

logger = logging.getLogger("spems.edge.zonemonitor")

class ZoneMonitor:
    """
    Advanced spatial rules engine running on Edge nodes.
    Analyzes tracked vehicle trajectories to detect geofenced restricted entries,
    illegal parking anomalies, and wrong-direction transits.
    """
    def __init__(self, parking_time_threshold_seconds: float = 3.0):
        self.parking_threshold = parking_time_threshold_seconds
        
        # Track history for illegal parking analysis: track_id -> (start_stationary_timestamp, coordinates)
        self.stationary_registry = {}
        
        # Track history for wrong-route direction analysis: track_id -> list of historic coordinates
        self.trajectory_registry = {}
        
        # Cache to prevent double-logging violations for the same track session
        self.logged_violations = set()

    @staticmethod
    def is_point_in_polygon(point: tuple, polygon: list) -> bool:
        """
        Ray-casting algorithm to determine if a coordinate falls inside a polygon.
        Point format: (x, y). Polygon format: [(x1, y1), (x2, y2), ...]
        """
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def evaluate_vehicle_rules(self, track_id: int, bbox: tuple, class_name: str, 
                               no_parking_zones: list, restricted_zones: list, 
                               allowed_direction_vector: tuple = (0, 1)) -> dict:
        """
        Runs the full spatial rules check on a tracked vehicle's coordinates.
        Returns a dictionary containing violation parameters if any rule is broken.
        """
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) // 2
        cy = y2 # Bottom center coordinate represents vehicle-road contact point
        current_time = time.time()

        # Update trajectory history for wrong-route checks
        if track_id not in self.trajectory_registry:
            self.trajectory_registry[track_id] = []
        self.trajectory_registry[track_id].append((cx, cy, current_time))
        
        # Prune older history to avoid memory leaks
        if len(self.trajectory_registry[track_id]) > 30:
            self.trajectory_registry[track_id].pop(0)

        # ----------------------------------------------------------------------------
        # Rule 1: Restricted-Area Entry Detection
        # ----------------------------------------------------------------------------
        for zone in restricted_zones:
            zone_id = zone["id"]
            zone_polygon = zone["polygon"]
            
            violation_key = f"{track_id}_restricted_{zone_id}"
            if violation_key not in self.logged_violations:
                if self.is_point_in_polygon((cx, cy), zone_polygon):
                    self.logged_violations.add(violation_key)
                    logger.warning(f"Vehicle {track_id} broke Restricted Entry in zone {zone_id}!")
                    return {
                        "track_id": track_id,
                        "violation_type": "Restricted_Zone_Entry",
                        "severity_level": "High",
                        "details": f"Unauthorized entry into geofenced restricted sector: {zone_id}"
                    }

        # ----------------------------------------------------------------------------
        # Rule 2: Illegal Parking Detection
        # ----------------------------------------------------------------------------
        # Check if vehicle center falls inside designated no-parking polygons
        in_parking_zone = False
        active_zone_id = None
        for zone in no_parking_zones:
            if self.is_point_in_polygon((cx, cy), zone["polygon"]):
                in_parking_zone = True
                active_zone_id = zone["id"]
                break

        violation_key = f"{track_id}_parking_{active_zone_id}"
        if in_parking_zone and violation_key not in self.logged_violations:
            if track_id not in self.stationary_registry:
                # Begin monitoring stationary duration
                self.stationary_registry[track_id] = {
                    "start_time": current_time,
                    "last_coords": (cx, cy)
                }
            else:
                record = self.stationary_registry[track_id]
                prev_cx, prev_cy = record["last_coords"]
                
                # Check if vehicle has actually remained stationary (moved less than 5 pixels)
                movement = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                if movement < 5.0:
                    stationary_duration = current_time - record["start_time"]
                    if stationary_duration >= self.parking_threshold:
                        self.logged_violations.add(violation_key)
                        logger.warning(f"Vehicle {track_id} broke Parking rules in zone {active_zone_id}!")
                        return {
                            "track_id": track_id,
                            "violation_type": "Illegal_Parking",
                            "severity_level": "Medium",
                            "details": f"Vehicle remained stationary for {stationary_duration:.1f}s inside zone: {active_zone_id}"
                        }
                else:
                    # Vehicle is moving, reset stopwatch
                    self.stationary_registry[track_id] = {
                        "start_time": current_time,
                        "last_coords": (cx, cy)
                    }
        else:
            # Not in no-parking zone, purge active timer
            self.stationary_registry.pop(track_id, None)

        # ----------------------------------------------------------------------------
        # Rule 3: Wrong-Route / Wrong-Way Direction Detection
        # ----------------------------------------------------------------------------
        trajectory = self.trajectory_registry[track_id]
        violation_key = f"{track_id}_wrong_way"
        if len(trajectory) >= 10 and violation_key not in self.logged_violations:
            # Measure overall displacement vector over last 10 frames
            start_cx, start_cy, _ = trajectory[0]
            end_cx, end_cy, _ = trajectory[-1]
            
            displacement_x = end_cx - start_cx
            displacement_y = end_cy - start_cy
            
            # Normalize vector
            magnitude = np.sqrt(displacement_x**2 + displacement_y**2)
            if magnitude > 30.0: # Ensure significant motion occurred
                dir_x = displacement_x / magnitude
                dir_y = displacement_y / magnitude
                
                # Dot product comparison against the allowed direction vector
                # e.g., if allowed is (0, 1) -> downward movement, dot product must be > 0
                dot_product = dir_x * allowed_direction_vector[0] + dir_y * allowed_direction_vector[1]
                
                # If dot product is strongly negative, vehicle is traveling wrong-way!
                if dot_product < -0.70:
                    self.logged_violations.add(violation_key)
                    logger.warning(f"Vehicle {track_id} traveling in WRONG DIRECTION!")
                    return {
                        "track_id": track_id,
                        "violation_type": "Restricted_Zone_Entry", # Standard DB categorizer
                        "severity_level": "High",
                        "details": f"Wrong-Route intrusion detected. Heading vector: [{dir_x:.2f}, {dir_y:.2f}]"
                    }

        return None
