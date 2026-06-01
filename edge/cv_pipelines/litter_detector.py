import cv2
import numpy as np
import time

class LitterDetector:
    """
    Real-Time Litter Action Detection Engine.
    Employs a spatial-temporal heuristic tracking "detaching objects" from
    pedestrians or vehicle bounding boxes. Avoids heavy 3D ConvNets, making
    it highly optimized for on-site Edge GPUs (NVIDIA Jetson).
    """
    def __init__(self, distance_threshold_pixels: float = 80.0, stationary_frame_limit: int = 15):
        # Pixel distance limit to correlate a new litter instance to a nearby subject
        self.distance_threshold = distance_threshold_pixels
        
        # Number of consecutive frames an object must remain stationary to be classified as discarded waste
        self.stationary_limit = stationary_frame_limit

        # Track history dictionary: garbage_track_id -> list of historic centers [(x, y, timestamp), ...]
        self.litter_trajectories = {}
        
        # Cache to prevent generating duplicate warnings for the same discarded item
        # Maps litter_track_id -> boolean status (True if logged)
        self.flagged_infractions = {}

    @staticmethod
    def calculate_euclidean_distance(pt1: tuple, pt2: tuple) -> float:
        return np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

    def analyze_objects(self, tracked_subjects: list, detected_waste: list, frame: np.ndarray) -> list:
        """
        Analyzes relationships between moving subjects (people, vehicles) and new/existing waste items.
        Returns a list of triggered violations containing evidence image data and coordinates.
        """
        active_violations = []

        # Loop through detected waste boxes (YOLOv8 classes: e.g. bottle, plastic, bag, garbage)
        for waste in detected_waste:
            w_id = waste["track_id"]
            w_bbox = waste["bbox"]
            w_center = ((w_bbox[0] + w_bbox[2]) // 2, (w_bbox[1] + w_bbox[3]) // 2)
            
            # If already logged, skip further validation
            if self.flagged_infractions.get(w_id, False):
                continue

            # Update spatial-temporal trajectory history
            if w_id not in self.litter_trajectories:
                self.litter_trajectories[w_id] = []
            self.litter_trajectories[w_id].append((w_center[0], w_center[1], time.time()))

            # Maintain history size to prevent memory leaks (keep last 50 frames)
            if len(self.litter_trajectories[w_id]) > 50:
                self.litter_trajectories[w_id].pop(0)

            trajectory = self.litter_trajectories[w_id]
            if len(trajectory) < 5:
                continue # Need at least 5 frames of history to evaluate velocity trends

            # 1. Evaluate velocity trend
            # If the item has stopped moving (variance of coordinates over last N frames is small)
            recent_points = np.array([ [pt[0], pt[1]] for pt in trajectory[-self.stationary_limit:] ])
            coord_variance = np.var(recent_points, axis=0) if len(recent_points) >= self.stationary_limit else [99.0, 99.0]
            
            # If coordinates are stable (variance < 5 pixels), it is stationary litter
            is_stationary = coord_variance[0] < 5.0 and coord_variance[1] < 5.0

            # 2. Correlate origin point with nearest subject
            if is_stationary and not self.flagged_infractions.get(w_id, False):
                origin_point = (trajectory[0][0], trajectory[0][1])
                
                closest_subject = None
                min_distance = float('inf')

                # Find nearest pedestrian/vehicle when the item first appeared
                for sub in tracked_subjects:
                    s_bbox = sub["bbox"]
                    s_center = ((s_bbox[0] + s_bbox[2]) // 2, (s_bbox[1] + s_bbox[3]) // 2)
                    dist = self.calculate_euclidean_distance(origin_point, s_center)
                    
                    if dist < min_distance:
                        min_distance = dist
                        closest_subject = sub

                # If the item originated from close proximity to a tracked person or car
                if closest_subject and min_distance < self.distance_threshold:
                    self.flagged_infractions[w_id] = True
                    
                    # Log violation details
                    violation_data = {
                        "violation_type": "Littering",
                        "severity_level": "Medium" if closest_subject["class_name"] == "person" else "High", # Higher fine if thrown from moving vehicle
                        "evidence_frame": frame.copy(),
                        "associated_plate": closest_subject.get("plate_number", None), # Plucked from ANPR tracker association if present
                        "subject_type": closest_subject["class_name"]
                    }
                    active_violations.append(violation_data)
                    print(f"[Litter Alert] Littering detected from {closest_subject['class_name']}! Detached item track: {w_id}")

        return active_violations
