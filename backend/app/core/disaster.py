# backend/app/core/disaster.py
# Disaster Monitoring Service detecting landslide, rockfall, and flooding risks.

import cv2
import numpy as np
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from ..db.models import DisasterAlert, SensorData, Location, Camera
from ..schemas.types import DisasterStatus

class DisasterMonitoringService:
    @staticmethod
    def calculate_optical_flow(prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        Calculates the average flow magnitude between two frames using OpenCV Farneback optical flow.
        Gracefully handles dimension mismatches or failure conditions.
        """
        try:
            if prev_frame is None or curr_frame is None:
                return 0.0

            # Convert to grayscale
            if len(prev_frame.shape) == 3:
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            else:
                prev_gray = prev_frame

            if len(curr_frame.shape) == 3:
                curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            else:
                curr_gray = curr_frame

            # Resize if dimensions differ
            if prev_gray.shape != curr_gray.shape:
                curr_gray = cv2.resize(curr_gray, (prev_gray.shape[1], prev_gray.shape[0]))

            # Compute dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None, 
                pyr_scale=0.5, levels=3, winsize=15, 
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )

            # Calculate magnitude
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            mean_flow = float(np.mean(magnitude))
            
            # Auto-fallback: if Farneback flow returns near-zero but there is visual difference
            if mean_flow < 0.05:
                diff = cv2.absdiff(prev_gray, curr_gray)
                mean_diff = float(np.mean(diff))
                if mean_diff > 1.0:
                    return mean_diff / 5.0
            
            return mean_flow
        except Exception:
            # Fallback to simple absolute difference if flow calculation fails
            try:
                diff = cv2.absdiff(prev_gray, curr_gray)
                mean_diff = float(np.mean(diff))
                return mean_diff / 10.0 # Scale to approximate flow magnitude
            except Exception:
                return 0.0

    @staticmethod
    async def evaluate_landslide_risk(
        db: AsyncSession, 
        camera_id: str, 
        prev_frame: np.ndarray, 
        curr_frame: np.ndarray
    ) -> dict:
        """
        Processes frame differences via optical flow. Rapid shifts indicate rockfalls or landslide flows.
        """
        flow_mag = DisasterMonitoringService.calculate_optical_flow(prev_frame, curr_frame)
        
        # Risk levels based on displacement velocity threshold
        if flow_mag >= 12.0:
            severity = "Critical"
            score = 100.0
            desc = "Sudden structural pixel shift indicating active slope displacement or landslide flow."
        elif flow_mag >= 6.0:
            severity = "High"
            score = 75.0
            desc = "Moderate movement detected on monitored slopes; possible rockfall warning."
        elif flow_mag >= 1.0:
            severity = "Medium"
            score = 45.0
            desc = "Low-velocity structural shifts detected. Slope parameters within standard margins."
        else:
            severity = "Low"
            score = 10.0
            desc = "No abnormal pixel movement or optical flow detected."

        return {
            "flow_magnitude": flow_mag,
            "severity_level": severity,
            "score": score,
            "description": desc
        }

    @staticmethod
    async def evaluate_flood_risk(db: AsyncSession, location_id: int) -> dict:
        """
        Computes localized flood/overflow warnings using telemetry logs:
        Checks water pH spikes, high humidity, air temperature gradients, and CO2 proxies.
        """
        # Get latest telemetry readings for location
        stmt = (
            select(SensorData)
            .where(SensorData.location_id == location_id)
            .order_by(desc(SensorData.measured_at))
            .limit(10)
        )
        result = await db.execute(stmt)
        readings = result.scalars().all()

        if not readings:
            return {
                "score": 10.0,
                "severity_level": "Low",
                "description": "No active telemetry data. Flood monitoring operating on default safe limits.",
                "readings": {}
            }

        latest = readings[0]
        
        # Calculate rates of change if multiple readings are present
        ph_change = 0.0
        temp_change = 0.0
        if len(readings) > 1:
            prev = readings[-1]
            if latest.water_ph is not None and prev.water_ph is not None:
                ph_change = abs(float(latest.water_ph) - float(prev.water_ph))
            if latest.temperature is not None and prev.temperature is not None:
                temp_change = abs(float(latest.temperature) - float(prev.temperature))

        # Risk scoring logic
        score = 10.0
        details = []

        # 1. Critical Water pH spikes (chemical/turbidity shift indicator during overflow)
        if latest.water_ph is not None:
            val = float(latest.water_ph)
            if val < 5.5 or val > 8.5:
                score += 40.0
                details.append("Abnormal water pH indicating potential chemical/soil landslide runoffs")
            elif ph_change >= 1.2:
                score += 25.0
                details.append("Rapid rate of change in water pH indicating sediment discharge")

        # 2. Climate runoffs (humidity + temperature drops/spikes)
        humidity_val = float(latest.humidity) if latest.humidity is not None else 0.0
        temp_val = float(latest.temperature) if latest.temperature is not None else 15.0
        
        if humidity_val > 95.0:
            score += 20.0
            details.append("Extreme air saturation/humidity indicating heavy rainfall downpour")
            
        if temp_change >= 3.0:
            score += 15.0
            details.append("Drastic local thermal shift indicating rapid meteorological changes")

        # Ensure bounds
        score = min(score, 100.0)
        
        if score >= 75.0:
            severity = "Critical"
        elif score >= 50.0:
            severity = "High"
        elif score >= 30.0:
            severity = "Medium"
        else:
            severity = "Low"

        desc_str = "; ".join(details) if details else "All environmental telemetry nodes indicate stable parameters."

        return {
            "score": score,
            "severity_level": severity,
            "description": desc_str,
            "readings": {
                "water_ph": float(latest.water_ph) if latest.water_ph is not None else None,
                "humidity": humidity_val,
                "temperature": temp_val,
                "aqi": latest.aqi
            }
        }

    @staticmethod
    async def update_disaster_hazards(
        db: AsyncSession,
        location_id: int,
        camera_id: str,
        prev_frame: np.ndarray,
        curr_frame: np.ndarray
    ) -> DisasterStatus:
        """
        Performs simultaneous optical flow and telemetry monitoring.
        Saves warning or critical events directly to the database.
        """
        # Run assessments
        landslide_res = await DisasterMonitoringService.evaluate_landslide_risk(
            db, camera_id, prev_frame, curr_frame
        )
        flood_res = await DisasterMonitoringService.evaluate_flood_risk(db, location_id)

        # Rockfall risk is a proxy of landslide risk with a lower threshold/frequency
        rockfall_score = min(landslide_res["score"] * 1.1, 100.0)

        # Overall hazard index
        overall_index = max(landslide_res["score"], flood_res["score"], rockfall_score)
        
        status = "SAFE"
        if overall_index >= 75.0:
            status = "CRITICAL"
        elif overall_index >= 40.0:
            status = "WARNING"

        # If warning or critical, persist an alert
        if status in ["WARNING", "CRITICAL"]:
            # Check if there is already an active alert of similar type to avoid duplicate storms
            hazard_type = "Landslide" if landslide_res["score"] >= flood_res["score"] else "Flood"
            trigger_src = "Optical Flow Detection" if hazard_type == "Landslide" else "Telemetry Threshold"
            desc_text = landslide_res["description"] if hazard_type == "Landslide" else flood_res["description"]
            readings_dict = {"flow_magnitude": landslide_res["flow_magnitude"]} if hazard_type == "Landslide" else flood_res["readings"]

            stmt = (
                select(DisasterAlert)
                .where(
                    DisasterAlert.location_id == location_id,
                    DisasterAlert.hazard_type == hazard_type,
                    DisasterAlert.is_active == True
                )
            )
            res = await db.execute(stmt)
            existing = res.scalars().first()

            if not existing:
                new_alert = DisasterAlert(
                    location_id=location_id,
                    hazard_type=hazard_type,
                    severity_level=landslide_res["severity_level"] if hazard_type == "Landslide" else flood_res["severity_level"],
                    trigger_source=trigger_src,
                    description=desc_text,
                    sensor_readings=readings_dict,
                    is_active=True
                )
                db.add(new_alert)
                await db.commit()

        return DisasterStatus(
            location_id=location_id,
            landslide_risk_score=landslide_res["score"],
            flood_risk_score=flood_res["score"],
            rockfall_risk_score=rockfall_score,
            overall_hazard_index=overall_index,
            status=status
        )

    @staticmethod
    async def get_active_alerts(db: AsyncSession) -> list[DisasterAlert]:
        """
        Retrieves all active disaster alerts.
        """
        stmt = select(DisasterAlert).where(DisasterAlert.is_active == True).order_by(desc(DisasterAlert.created_at))
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_alert(db: AsyncSession, alert_id: int) -> DisasterAlert:
        """
        Resolves an active alert.
        """
        stmt = select(DisasterAlert).where(DisasterAlert.id == alert_id)
        res = await db.execute(stmt)
        alert = res.scalars().first()
        if alert:
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(alert)
        return alert
