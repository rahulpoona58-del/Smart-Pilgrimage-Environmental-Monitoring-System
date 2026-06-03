# edge/utils/vitals_exporter.py
# Edge Diagnostics Exporter: Serves hardware metrics to Prometheus.

import os
import time
import sqlite3
import http.server
import socketserver
import urllib.parse

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP service that scrapes Jetson diagnostic metrics and exposes them in Prometheus standard formats."""
    
    def log_message(self, format, *args):
        # Silence HTTP request log print statements
        return

    def get_failsafe_buffer_count(self) -> int:
        """Retrieves count of cached offline entries in the local SQLite buffer."""
        db_path = "buffer/edge_buffer.db"
        if not os.path.exists(db_path):
            db_path = "database/buffer.db"
        if not os.path.exists(db_path):
            return 0
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vehicle_logs;")
            log_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM violations;")
            violation_count = cursor.fetchone()[0]
            conn.close()
            return log_count + violation_count
        except Exception:
            return 0

    def get_jetson_core_temperature(self, zone: str) -> float:
        """Scrapes standard Linux system thermal zones (fallback to mock values on non-Linux architectures)."""
        thermal_path = f"/sys/class/thermal/thermal_zone{zone}/temp"
        if os.path.exists(thermal_path):
            try:
                with open(thermal_path, "r") as f:
                    temp_raw = int(f.read().strip())
                    return temp_raw / 1000.0
            except Exception:
                pass
        # Static mock fallbacks representing active operational temperature profiles
        if zone == "0": # CPU
            return 44.5
        elif zone == "1": # GPU
            return 42.0
        return 38.0

    def get_vram_allocation_bytes(self) -> int:
        """Mock reading memory utilization metrics on the edge module."""
        return 2147483648 # 2GB VRAM allocated

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.end_headers()

        # Scrape and build Prometheus gauges
        cpu_temp = self.get_jetson_core_temperature("0")
        gpu_temp = self.get_jetson_core_temperature("1")
        vram_bytes = self.get_vram_allocation_bytes()
        buffer_records = self.get_failsafe_buffer_count()

        metrics_payload = (
            f"# HELP jetson_core_temperature Core thermal readings in Celsius\n"
            f"# TYPE jetson_core_temperature gauge\n"
            f"jetson_core_temperature{{node=\"EDGE-GK-001\",zone=\"CPU\"}} {cpu_temp:.2f}\n"
            f"jetson_core_temperature{{node=\"EDGE-GK-001\",zone=\"GPU\"}} {gpu_temp:.2f}\n\n"
            f"# HELP jetson_gpu_memory_used_bytes Memory utilization in bytes\n"
            f"# TYPE jetson_gpu_memory_used_bytes gauge\n"
            f"jetson_gpu_memory_used_bytes{{node=\"EDGE-GK-001\"}} {vram_bytes}\n\n"
            f"# HELP jetson_failsafe_buffer_records Volume of cached records in offline SQLite buffer\n"
            f"# TYPE jetson_failsafe_buffer_records gauge\n"
            f"jetson_failsafe_buffer_records{{node=\"EDGE-GK-001\"}} {buffer_records}\n"
        )

        self.wfile.write(metrics_payload.encode("utf-8"))

def start_metrics_server(port: int = 9100):
    """Launches the lightweight HTTP metrics server on a background port."""
    handler = MetricsHandler
    # Set immediate socket reuse to prevent port-in-use errors on fast restarts
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
            print(f"[Monitoring] Diagnostic metrics server listening on: http://localhost:{port}/metrics")
            httpd.serve_forever()
    except Exception as e:
        print(f"[Monitoring Error] Failed to start HTTP server: {e}")

if __name__ == "__main__":
    start_metrics_server(9100)
