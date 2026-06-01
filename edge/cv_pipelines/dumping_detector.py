# edge/cv_pipelines/dumping_detector.py
# Milestone 9: Illegal Dumping and River Pollution Detection Engine.

import cv2
import numpy as np
import time
import logging

logger = logging.getLogger("spems.edge.dumping_detector")

class DumpingDetector:
    """
    Real-Time Illegal Dumping and Waterbody Pollution Detection Engine.
    Employs spatial-temporal heuristics to detect static open dumping piles,
    plastic waste hotspots, and geofenced river contamination events on Edge GPUs.
    """
    def __init__(self, 
                 distance_threshold_pixels: float = 100.0, 
                 stationary_frame_limit: int = 5,
                 pile_area_threshold: float = 2000.0):
        # Pixel distance limit to merge close waste items or correlate them to zones
        self.distance_threshold = distance_threshold_pixels
        self.stationary_limit = stationary_frame_limit
        self.pile_area_threshold = pile_area_threshold
        
        # Track history for waste items: waste_track_id -> list of historic coordinates [(cx, cy, area, timestamp), ...]
        self.waste_trajectories = {}
        
        # Cache to prevent duplicate warnings for the same dumping instance
        self.logged_violations = set()

    @staticmethod
    def calculate_euclidean_distance(pt1: tuple, pt2: tuple) -> float:
        return np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

    @staticmethod
    def is_point_in_polygon(point: tuple, polygon: list) -> bool:
        """
        Ray-casting algorithm to determine if coordinate falls inside a geofenced zone polygon.
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

    def analyze_waste(self, 
                      detected_waste: list, 
                      frame: np.ndarray,
                      river_zones: list, 
                      designated_bin_zones: list,
                      camera_coords: tuple = (30.6500, 79.0050)) -> list:
        """
        Processes frame predictions for waste classes and evaluates compliance rules.
        Returns a list of environmental violations if dumping or water pollution is detected.
        """
        active_violations = []
        current_time = time.time()

        for waste in detected_waste:
            w_id = waste["track_id"]
            w_bbox = waste["bbox"] # (x1, y1, x2, y2)
            class_name = waste.get("class_name", "plastic") # default to plastic
            
            x1, y1, x2, y2 = w_bbox
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)

            # Update history
            if w_id not in self.waste_trajectories:
                self.waste_trajectories[w_id] = []
            self.waste_trajectories[w_id].append((cx, cy, area, current_time))

            # Maintain history size to prevent memory leaks
            if len(self.waste_trajectories[w_id]) > 50:
                self.waste_trajectories[w_id].pop(0)

            trajectory = self.waste_trajectories[w_id]
            if len(trajectory) < 5:
                continue # Need history to establish stability

            # Evaluate coordinate variance to ensure item has stopped moving
            recent_points = np.array([ [pt[0], pt[1]] for pt in trajectory[-self.stationary_limit:] ])
            coord_variance = np.var(recent_points, axis=0) if len(recent_points) >= self.stationary_limit else [99.0, 99.0]
            is_stationary = coord_variance[0] < 5.0 and coord_variance[1] < 5.0

            if not is_stationary:
                continue

            # ------------------------------------------------------------------------
            # Rule 1: River Pollution Detection (Waterbody Intrusion)
            # ------------------------------------------------------------------------
            in_river = False
            active_river_id = None
            for zone in river_zones:
                if self.is_point_in_polygon((cx, cy), zone["polygon"]):
                    in_river = True
                    active_river_id = zone["id"]
                    break

            violation_key_river = f"{w_id}_river_{active_river_id}"
            if in_river and violation_key_river not in self.logged_violations:
                self.logged_violations.add(violation_key_river)
                logger.warning(f"Waterbody pollution detected in river zone {active_river_id}! Item {w_id}")
                
                # Geotag calculation: Camera georeference point + perspective scale factor
                lat_offset = (cy - frame.shape[0] / 2) * -0.00001
                lng_offset = (cx - frame.shape[1] / 2) * 0.00001
                geotag = (camera_coords[0] + lat_offset, camera_coords[1] + lng_offset)

                violation_data = {
                    "violation_type": "River_Pollution",
                    "severity_level": "High",
                    "evidence_frame": frame.copy(),
                    "details": f"Waterbody contamination: Plastic/bulk waste floating inside river zone {active_river_id}",
                    "geotag": geotag,
                    "associated_plate": None
                }
                active_violations.append(violation_data)
                continue

            # ------------------------------------------------------------------------
            # Rule 2: Open Dumping & Plastic Accumulation Detection
            # ------------------------------------------------------------------------
            # Open dumping is flagged if waste is stationary outside designated bin zones
            in_bin_zone = False
            for zone in designated_bin_zones:
                if self.is_point_in_polygon((cx, cy), zone["polygon"]):
                    in_bin_zone = True
                    break

            # If waste is NOT inside a designated bin zone, it is unauthorized dumping
            if not in_bin_zone:
                # Differentiate between minor Littering (small size) and Bulk Dumping (large area or growing pile)
                is_bulk = area >= self.pile_area_threshold
                
                # Check for dynamic growth: if the area has grown significantly over the trajectory
                initial_area = trajectory[0][2]
                current_area = trajectory[-1][2]
                growth_rate = current_area / initial_area if initial_area > 0 else 1.0
                is_growing_pile = growth_rate > 1.4 and current_area > 800

                violation_type = "Littering"
                severity = "High" if (is_bulk or is_growing_pile) else "Medium"
                detail_msg = f"Bulk illegal garbage pile dumping detected. Size: {area:.0f}px" if is_bulk else (
                    f"Growing waste accumulation pile detected (growth: {growth_rate:.1f}x)" if is_growing_pile else
                    f"Open plastic waste dumping detected: Class={class_name}"
                )

                violation_key_dumping = f"{w_id}_dumping"
                if violation_key_dumping not in self.logged_violations:
                    self.logged_violations.add(violation_key_dumping)
                    logger.warning(f"Illegal dumping infraction: {detail_msg}! Item {w_id}")

                    # Geotag calculation: Camera georeference point + perspective scale factor
                    lat_offset = (cy - frame.shape[0] / 2) * -0.00001
                    lng_offset = (cx - frame.shape[1] / 2) * 0.00001
                    geotag = (camera_coords[0] + lat_offset, camera_coords[1] + lng_offset)

                    violation_data = {
                        "violation_type": violation_type,
                        "severity_level": severity,
                        "evidence_frame": frame.copy(),
                        "details": detail_msg,
                        "geotag": geotag,
                        "associated_plate": None
                    }
                    active_violations.append(violation_data)

        return active_violations
