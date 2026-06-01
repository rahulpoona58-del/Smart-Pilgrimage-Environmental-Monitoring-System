import time
import random
import requests
from datetime import datetime, timezone

API_URL = "http://localhost:8000/api/v1/telemetry"

LOCATIONS = [1, 2, 3] # Gaurikund, Badrinath, Gangotri
DEVICES = ["IOT-GK-A1", "IOT-BD-B1", "IOT-GT-C1"]

def simulate_iot_telemetry():
    """Continuously registers randomized IoT telemetries to verify backend controllers."""
    print("[Simulator] Launching atmospheric telemetry data feed simulator...")
    
    try:
        while True:
            for i, loc in enumerate(LOCATIONS):
                dev = DEVICES[i]
                
                # Base parameters with seasonal bounds
                pm25 = round(random.uniform(5.0, 35.0), 2)
                pm10 = round(pm25 * random.uniform(1.5, 2.2), 2)
                aqi = int(pm25 * 3.1)
                
                temp = round(random.uniform(4.0, 18.0), 2)
                humid = round(random.uniform(45.0, 85.0), 2)
                co2 = round(random.uniform(380.0, 420.0), 2)
                ph = round(random.uniform(7.1, 8.2), 2)

                payload = {
                    "location_id": loc,
                    "device_id": dev,
                    "pm25": pm25,
                    "pm10": pm10,
                    "aqi": aqi,
                    "temperature": temp,
                    "humidity": humid,
                    "co2": co2,
                    "water_ph": ph,
                    "measured_at": datetime.now(timezone.utc).isoformat() + "Z"
                }

                try:
                    response = requests.post(API_URL, json=payload, timeout=3.0)
                    if response.status_code == 201:
                        print(f"[IoT Broadcast] Dispatched telemetry for {dev}: AQI={aqi}, Temp={temp}°C")
                except requests.RequestException as e:
                    print(f"[IoT Broadcast Connection Error] Unable to reach backend API: {e}")
                    
            time.sleep(5.0) # Send updates every 5 seconds
            
    except KeyboardInterrupt:
        print("[Simulator] Exiting IoT stream harness.")

if __name__ == "__main__":
    # Add simple delay to allow FastAPI containers to initialize
    time.sleep(2.0)
    simulate_iot_telemetry()
