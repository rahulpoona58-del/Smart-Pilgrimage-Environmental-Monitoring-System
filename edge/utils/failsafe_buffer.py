import sqlite3
import json
import os
import logging

logger = logging.getLogger("spems.edge.buffer")

class FailsafeBuffer:
    """
    Local SQLite buffer database.
    Stores metadata events when offline, synchronizing logs once remote REST APIs are reachable.
    """
    def __init__(self, db_path: str = "buffer/edge_buffer.db"):
        self.db_path = db_path
        
        # Ensure containing directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._initialize_database()

    def _initialize_database(self):
        """Creates buffer queues if they do not exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create a table for vehicle transit logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    location_id INTEGER NOT NULL,
                    log_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_confidence REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create a table for environmental violations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    camera_id TEXT NOT NULL,
                    plate_number TEXT,
                    violation_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    evidence_image_path TEXT NOT NULL,
                    violation_coordinates TEXT NOT NULL, -- JSON string representation
                    violation_timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def buffer_vehicle_log(self, plate: str, camera_id: str, location_id: int, log_type: str, timestamp: str, confidence: float):
        """Pushes an entry/exit record into the SQLite buffer table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO vehicle_logs (plate_number, camera_id, location_id, log_type, timestamp, raw_confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (plate, camera_id, location_id, log_type, timestamp, confidence))
                conn.commit()
            logger.info(f"[Buffer Cache] Cached offline vehicle log: {plate}")
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to write offline vehicle log: {e}")

    def buffer_violation(self, location_id: int, camera_id: str, plate: str, v_type: str, severity: str, img_path: str, coords: tuple, timestamp: str):
        """Pushes an environmental infraction event into the SQLite buffer table."""
        try:
            coords_json = json.dumps({"lat": coords[0], "lng": coords[1]})
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO violations (location_id, camera_id, plate_number, violation_type, severity_level, evidence_image_path, violation_coordinates, violation_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (location_id, camera_id, plate, v_type, severity, img_path, coords_json, timestamp))
                conn.commit()
            logger.info(f"[Buffer Cache] Cached offline violation: {v_type} for {plate if plate else 'Pedestrian'}")
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to cache offline violation event: {e}")

    def fetch_all_buffered_logs(self) -> list:
        """Fetches all items currently cached in the vehicle logs table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vehicle_logs ORDER BY id ASC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to query buffered logs: {e}")
            return []

    def fetch_all_buffered_violations(self) -> list:
        """Fetches all items currently cached in the violations table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM violations ORDER BY id ASC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to query buffered violations: {e}")
            return []

    def remove_buffered_logs(self, record_ids: list):
        """Prunes uploaded records from the vehicle logs cache."""
        if not record_ids:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in record_ids)
                cursor.execute(f"DELETE FROM vehicle_logs WHERE id IN ({placeholders})", record_ids)
                conn.commit()
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to purge vehicle logs from buffer: {e}")

    def remove_buffered_violations(self, record_ids: list):
        """Prunes uploaded records from the violations cache."""
        if not record_ids:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" for _ in record_ids)
                cursor.execute(f"DELETE FROM violations WHERE id IN ({placeholders})", record_ids)
                conn.commit()
        except Exception as e:
            logger.error(f"[Buffer Error] Failed to purge violations from buffer: {e}")
