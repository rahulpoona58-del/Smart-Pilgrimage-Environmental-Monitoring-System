# edge/utils/camera_ingest.py
# CCTV Video Ingestion System: Multi-Threaded, Resilient Stream Manager.

import cv2
import time
import logging
import threading
import os
import numpy as np
from typing import Dict, Union, Callable

logger = logging.getLogger("spems.edge.ingest")

class CameraStreamWorker:
    """
    Manages a single RTSP network stream or local MP4 file.
    Runs on an independent thread, maintaining a non-blocking queue of the latest decoded frame
    with built-in exponential backoff reconnection recovery.
    """
    def __init__(self, camera_id: str, stream_url: Union[str, int], max_buffer_size: int = 1):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.max_buffer = max_buffer_size
        
        # Frame state
        self.latest_frame = None
        self.fps = 0.0
        self.frame_count = 0
        self.dropped_frames = 0
        
        # Operational flags
        self.is_running = False
        self.is_connected = False
        self.thread = None
        self.shutdown_flag = threading.Event()
        
        # Lock to ensure thread-safe read/write on the frame buffer
        self.frame_lock = threading.Lock()

    def start(self):
        """Spins up the dedicated background capture thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.shutdown_flag.clear()
        self.thread = threading.Thread(target=self._capture_loop, name=f"CamIngest-{self.camera_id}", daemon=True)
        self.thread.start()
        logger.info(f"Stream worker started for camera: {self.camera_id}")

    def stop(self):
        """Signals the capture thread to terminate and joins it."""
        self.is_running = False
        self.shutdown_flag.set()
        if self.thread:
            self.thread.join(timeout=3.0)
            logger.info(f"Stream worker stopped for camera: {self.camera_id}")

    def get_latest_frame(self) -> np.ndarray:
        """Thread-safe retrieval of the latest decoded frame matrix."""
        with self.frame_lock:
            frame = self.latest_frame
            self.latest_frame = None # Consume frame to prevent double-processing
            return frame

    def _capture_loop(self):
        """Core frame extraction loop executing backoff reconnection loops."""
        reconnect_delay = 1.0
        max_reconnect_delay = 60.0
        is_file = isinstance(self.stream_url, str) and os.path.exists(self.stream_url)

        while self.is_running and not self.shutdown_flag.is_set():
            logger.info(f"Connecting to video stream source: {self.stream_url}...")
            cap = cv2.VideoCapture(self.stream_url)
            
            # Verify stream interface connection
            if cap.isOpened():
                self.is_connected = True
                reconnect_delay = 1.0 # Reset backoff delay on successful connection
                logger.info(f"Successfully connected to stream: {self.camera_id}")
            else:
                self.is_connected = False
                logger.warning(f"Connection failed for {self.camera_id}. Retrying in {reconnect_delay:.1f}s...")
                cap.release()
                self.shutdown_flag.wait(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay) # Exponential backoff
                continue

            last_fps_time = time.time()
            local_frame_count = 0
            
            # Get video file frame rate properties to pace simulation streams
            fps_prop = cap.get(cv2.CAP_PROP_FPS)
            frame_delay = 1.0 / fps_prop if (is_file and fps_prop and fps_prop > 0.0) else 0.0

            # Decode loop
            while self.is_running and not self.shutdown_flag.is_set():
                t_start = time.time()
                ret, frame = cap.read()
                
                if not ret:
                    # If it's a file, break loop and do not flag error unless shutdown
                    if is_file:
                        logger.info(f"Local video file reached EOF for camera: {self.camera_id}")
                    else:
                        logger.warning(f"Stream buffer empty or connection dropped on camera: {self.camera_id}")
                    self.is_connected = False
                    break

                self.frame_count += 1
                local_frame_count += 1

                # Calculate real-time FPS
                current_time = time.time()
                elapsed = current_time - last_fps_time
                if elapsed >= 2.0: # Update FPS metrics every 2s
                    self.fps = local_frame_count / elapsed
                    local_frame_count = 0
                    last_fps_time = current_time
                    logger.debug(f"Camera {self.camera_id} metrics: FPS={self.fps:.1f}, Frames Decoded={self.frame_count}")

                # Thread-safe buffer update: replace old frame with latest to avoid queue lag
                with self.frame_lock:
                    if self.latest_frame is not None:
                        self.dropped_frames += 1
                    self.latest_frame = frame

                # Throttle file-based stream reads to emulate normal frame rate
                if is_file and frame_delay > 0.0:
                    t_elapsed = time.time() - t_start
                    sleep_time = frame_delay - t_elapsed
                    if sleep_time > 0.0:
                        self.shutdown_flag.wait(sleep_time)

            cap.release()
            self.is_connected = False
            
            # Wait before attempting connection recovery
            if self.is_running:
                logger.info(f"Reconnecting camera {self.camera_id} in {reconnect_delay}s...")
                self.shutdown_flag.wait(reconnect_delay)


class MultiCameraIngestManager:
    """
    Coordinates ingestion across multiple concurrent cameras (local files and RTSP URLs).
    Exposes unified metrics and frame fetch handlers.
    """
    def __init__(self):
        self.workers: Dict[str, CameraStreamWorker] = {}

    def register_camera(self, camera_id: str, url: Union[str, int]):
        """Creates and indexes a new camera stream worker."""
        if camera_id in self.workers:
            logger.warning(f"Camera {camera_id} already registered. Skipping.")
            return
        
        worker = CameraStreamWorker(camera_id, url)
        self.workers[camera_id] = worker
        logger.info(f"Registered camera {camera_id} in stream manager.")

    def start_all_streams(self):
        """Starts background capturing threads for all registered cameras."""
        for worker in self.workers.values():
            worker.start()
        logger.info("All camera ingestion streams started.")

    def stop_all_streams(self):
        """Gracefully stops all background threads."""
        for worker in self.workers.values():
            worker.stop()
        logger.info("All camera ingestion streams stopped.")

    def fetch_frame(self, camera_id: str) -> np.ndarray:
        """Retrieves latest frame from a specific camera node."""
        worker = self.workers.get(camera_id)
        if worker:
            return worker.get_latest_frame()
        return None

    def get_ingest_metrics(self) -> dict:
        """Gathers runtime metrics (FPS, drops, connection status) for dashboard consumption."""
        metrics = {}
        for cid, worker in self.workers.items():
            metrics[cid] = {
                "is_connected": worker.is_connected,
                "fps": round(worker.fps, 1),
                "total_decoded_frames": worker.frame_count,
                "dropped_frames": worker.dropped_frames
            }
        return metrics
