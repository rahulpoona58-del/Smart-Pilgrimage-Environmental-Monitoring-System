# run_mvp.py
# Master Orchestrator: Boots the unified SPEMS MVP on a single laptop.

import subprocess
import sys
import time
import os
import threading

def print_banner():
    print("==================================================")
    print("        SPEMS - LOCAL MVP ORCHESTRATOR            ")
    print("==================================================")
    print("Starting all integrated open-source AI microservices...")
    print("Press Ctrl+C to shutdown all running modules cleanly.")
    print("==================================================")

def run_service(command: list, name: str, cwd: str = "."):
    """Starts a subprocess and prints its console output with a prefix."""
    print(f"[Launcher] Starting service: '{name}'...")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd
        )
        
        # Read and print outputs in a background thread to prevent blocking
        def read_output():
            for line in iter(process.stdout.readline, ''):
                print(f"[{name}] {line.strip()}")
            process.stdout.close()
            
        threading.Thread(target=read_output, daemon=True).start()
        return process
    except Exception as e:
        print(f"[Launcher Error] Failed to start '{name}': {e}")
        return None

def main():
    print_banner()
    
    processes = []
    
    # 1. Initialize directories
    os.makedirs("database", exist_ok=True)
    os.makedirs("data/evidence", exist_ok=True)
    os.makedirs("static/evidence", exist_ok=True)

    # 2. Boot up local FastAPI backend server
    # Uses Uvicorn to host the API on port 8000
    # To run on a single laptop without needing heavy Postgres configs, the backend is 
    # fully compatible with SQLite databases by default if the DATABASE_URL environment is not set.
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    backend_proc = run_service(backend_cmd, "FastAPI Backend")
    if backend_proc:
        processes.append(backend_proc)
    
    # Wait for the backend to start up
    time.sleep(3.0)

    # 3. Start IoT sensor telemetry simulator
    # Emits AQI, PM2.5, and pH telemetry to port 8000
    iot_cmd = [sys.executable, "data_simulators/mock_iot_sensors.py"]
    iot_proc = run_service(iot_cmd, "IoT Simulator")
    if iot_proc:
        processes.append(iot_proc)

    # 4. Start the live edge tracking & litter simulation pipeline
    # Simulates roadway transits, tracks objects, and posts tickets to backend API
    litter_cmd = [sys.executable, "test_littering_detection.py"]
    litter_proc = run_service(litter_cmd, "Edge AI Tracker")
    if litter_proc:
        processes.append(litter_proc)

    # Keep orchestrator alive until keyboard interrupt
    try:
        print("\n[Orchestrator] All microservices are active. Monitoring feeds...")
        print("[Orchestrator] Access API documentation at: http://127.0.0.1:8000/docs\n")
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n[Shutdown] Terminating all running microservices...")
        for p in processes:
            if p:
                p.terminate()
        print("[Shutdown] All processes closed cleanly.")

if __name__ == "__main__":
    main()
