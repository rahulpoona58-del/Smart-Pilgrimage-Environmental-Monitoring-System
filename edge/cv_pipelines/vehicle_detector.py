# edge/cv_pipelines/vehicle_detector.py
# Milestone 3: YOLO-Based Vehicle Detection Module.

import cv2
import numpy as np
import logging
from ultralytics import YOLO

# Import local Ingestion Manager from Milestone 2
from ..utils.camera_ingest import MultiCameraIngestManager

logger = logging.getLogger("spems.edge.detector")

class LocalVehicleDetector:
    """
    Handles real-time vehicle classification and visual boundary logging.
    Ingests frames dynamically from MultiCameraIngestManager, filters classes,
    applies confidence thresholds, and computes vehicle volumes.
    """
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.35):
        self.conf_threshold = conf_threshold
        
        # Target COCO class mappings: 2 (car), 3 (motorcycle), 5 (bus), 7 (truck)
        self.target_classes = [2, 3, 5, 7]
        
        # Load pre-trained YOLOv8 weights (cached locally)
        logger.info(f"Loading YOLOv8 model weights from: {model_path}")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model weights: {e}")
            raise

    def process_camera_frame(self, frame: np.ndarray) -> tuple:
        """
        Runs YOLOv8 model inference on the frame matrix.
        Filters for vehicles, draws colored bounding boxes, and returns the processed frame and vehicle counts.
        """
        if frame is None or frame.size == 0:
            return frame, 0

        # Execute object detection (conf=self.conf_threshold filters out low-confidence inputs)
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        vehicle_count = 0
        
        if not results or len(results[0].boxes) == 0:
            return frame, 0

        result = results[0]
        boxes = result.boxes

        for box in boxes:
            cls_id = int(box.cls[0].item())
            
            # Check if classified object index matches target vehicle profiles
            if cls_id in self.target_classes:
                vehicle_count += 1
                
                # Bounding box coordinates
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, coords)
                
                conf = float(box.conf[0].item())
                class_name = self.model.names[cls_id]

                # Draw bounding boxes (BGR: Emerald Green, Thickness: 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (16, 185, 129), 2)
                
                # Draw small background text box to improve label legibility
                label = f"{class_name.upper()} {conf*100:.1f}%"
                (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(frame, (x1, y1 - 20), (x1 + label_w, y1), (16, 185, 129), -1)
                
                # Draw label text (White)
                cv2.putText(frame, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw vehicle counter overlay in top left corner (BGR: Dark Navy)
        cv2.rectangle(frame, (10, 10), (240, 50), (15, 20, 32), -1)
        cv2.putText(frame, f"VEHICLES DETECTED: {vehicle_count}", (20, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        logger.debug(f"Frame analysis complete. Classified {vehicle_count} active vehicles.")
        return frame, vehicle_count
