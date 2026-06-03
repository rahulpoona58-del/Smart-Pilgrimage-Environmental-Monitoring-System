import cv2
import numpy as np
from ultralytics import YOLO

class VehicleTracker:
    """
    Manages vehicle detection and track correlation across frames using YOLOv8.
    Integrates ByteTrack tracker logic to persist vehicle identity (track_ids).
    """
    def __init__(self, model_path: str = "models/yolov8n.pt", conf_threshold: float = 0.35, iou_threshold: float = 0.45):
        # Load the pre-trained YOLOv8 model (nano/small recommended for edge)
        self.model = YOLO(model_path)
        self.conf = conf_threshold
        self.iou = iou_threshold
        
        # Vehicle classes standard in COCO dataset: 2 (car), 3 (motorcycle), 5 (bus), 7 (truck)
        self.vehicle_classes = [2, 3, 5, 7]

    def detect_and_track(self, frame: np.ndarray):
        """
        Runs YOLOv8 model inference on the frame, performing object tracking.
        Returns a list of tracked vehicles containing: bounding box, track ID, vehicle class, and confidence score.
        """
        # Run inference using built-in ByteTrack tracker
        # persist=True maintains tracks across frames
        results = self.model.track(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            classes=self.vehicle_classes,
            persist=True,
            verbose=False
        )

        tracked_objects = []
        
        if not results or len(results) == 0:
            return tracked_objects

        result = results[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return tracked_objects

        for box in boxes:
            # Check if track ID exists (objects successfully tracked)
            if box.id is None:
                continue
                
            track_id = int(box.id[0].item())
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            
            # Extract bounding box coordinates [x1, y1, x2, y2]
            coords = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, coords)

            class_name = self.model.names[cls_id]

            tracked_objects.append({
                "track_id": track_id,
                "bbox": (x1, y1, x2, y2),
                "class_name": class_name,
                "class_id": cls_id,
                "confidence": conf
            })

        return tracked_objects

