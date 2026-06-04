import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ..db.models import Violation, Vehicle, SensorData, Location

class ComplianceScoringEngine:
    """
    Environmental Compliance & Scoring Engine (ECSE).
    Implements mathematical scoring models for Vehicles, Locations, and Shrines.
    """
    
    # ----------------------------------------------------------------------------
    # 1. VEHICLE COMPLIANCE MODEL
    # ----------------------------------------------------------------------------
    @staticmethod
    async def calculate_vehicle_compliance_score(db: AsyncSession, plate_number: str) -> dict:
        """
        Calculates a vehicle's compliance score based on chronological infractions.
        Formula:
            S_v = max(0, 100 - sum(Base_Penalty * Repeat_Multiplier))
        Repeat violations within 30 days trigger multipliers (1.5x, 2.0x).
        """
        # Base penalty rules
        PENALTY_MAP = {
            "Littering": 15,
            "Illegal_Parking": 10,
            "Restricted_Zone_Entry": 25,
            "River_Pollution": 35,
            "Overcrowding": 5 # Not typically linked to individual vehicle
        }

        # Query all approved or pending violations linked to vehicle
        query = select(Violation).where(
            (Violation.plate_number == plate_number) & 
            (Violation.status != "DISMISSED")
        ).order_by(Violation.violation_timestamp.asc())
        
        result = await db.execute(query)
        infractions = result.scalars().all()

        score = 100
        history_log = []
        violations_timeline = []

        for idx, v in enumerate(infractions):
            v_type = v.violation_type
            v_time = v.violation_timestamp
            base_penalty = PENALTY_MAP.get(v_type, 10)

            # Determine repeat infraction multiplier within a rolling 30-day window
            multiplier = 1.0
            
            # Compare with previous infractions in timeline
            recent_repeats = [
                prev_time for prev_time in violations_timeline 
                if (v_time - prev_time) <= timedelta(days=30)
            ]
            
            if len(recent_repeats) == 1:
                multiplier = 1.5
            elif len(recent_repeats) >= 2:
                multiplier = 2.0

            deduction = int(base_penalty * multiplier)
            score = max(0, score - deduction)
            
            violations_timeline.append(v_time)
            history_log.append({
                "violation_id": v.id,
                "type": v_type,
                "timestamp": v_time.isoformat(),
                "base_penalty": base_penalty,
                "multiplier": multiplier,
                "deduction": deduction
            })

        # Update Vehicle Registry ratings
        query_vehicle = select(Vehicle).where(Vehicle.plate_number == plate_number)
        res_vehicle = await db.execute(query_vehicle)
        vehicle = res_vehicle.scalars().first()

        risk_rating = "Low"
        if score <= 45:
            risk_rating = "High"
        elif score <= 75:
            risk_rating = "Medium"

        if vehicle:
            vehicle.compliance_score = score
            vehicle.risk_rating = risk_rating
            db.add(vehicle)
            await db.commit()

        return {
            "plate_number": plate_number,
            "compliance_score": score,
            "risk_rating": risk_rating,
            "total_violations": len(infractions),
            "penalty_history": history_log
        }

    # ----------------------------------------------------------------------------
    # 2. LOCATION ENVIRONMENTAL MODEL
    # ----------------------------------------------------------------------------
    @staticmethod
    async def calculate_location_compliance_score(db: AsyncSession, location_id: int) -> dict:
        """
        Calculates a composite location green rating (0-100) combining three indices:
          1. Air Quality Score (A_score): Derived from latest 24h average AQI.
          2. Waste Score (W_score): Deductions based on active littering events.
          3. Congestion Score (C_score): Overoccupancy ratios.
        Formula:
          Composite = 0.35 * A_score + 0.40 * W_score + 0.25 * C_score
        """
        query_loc = select(Location).where(Location.id == location_id)
        res_loc = await db.execute(query_loc)
        loc = res_loc.scalars().first()
        if not loc:
            return {"error": "Location not found"}

        # --- 1. Compute Air Quality Score ---
        # Query sensor data from last 24 hours
        time_limit = datetime.now(timezone.utc) - timedelta(hours=24)
        query_aqi = select(func.avg(SensorData.aqi)).where(
            (SensorData.location_id == location_id) & 
            (SensorData.measured_at >= time_limit)
        )
        res_aqi = await db.execute(query_aqi)
        avg_aqi = res_aqi.scalar() or 25.0 # default clean baseline if no sensors

        # AQI scaling: 0-50 (Good) -> score 100; 300+ (Hazardous) -> score 0
        a_score = int(max(0, 100 - (avg_aqi * 0.3)))

        # --- 2. Compute Waste Compliance Score ---
        # Deduct based on number of uncleared violations in last 7 days
        violation_limit = datetime.now(timezone.utc) - timedelta(days=7)
        query_v = select(func.count(Violation.id)).where(
            (Violation.location_id == location_id) & 
            (Violation.violation_timestamp >= violation_limit) &
            (Violation.status != "DISMISSED")
        )
        res_v = await db.execute(query_v)
        violation_count = res_v.scalar() or 0
        
        # Deduct 10 points per infraction, min score 0
        w_score = int(max(0, 100 - (violation_count * 10)))

        # --- 3. Compute Congestion Score ---
        # Assess current occupancy against capacity limits
        current = loc.pedestrian_capacity_limit # simulated proxy
        capacity = loc.pedestrian_capacity_limit
        
        c_score = 100
        if current > capacity:
            excess_ratio = (current - capacity) / capacity
            c_score = int(max(0, 100 - (excess_ratio * 100)))

        # --- 4. Trend Analysis (Rolling 24h vs previous 24h-48h) ---
        time_limit_prev = datetime.now(timezone.utc) - timedelta(hours=48)
        query_aqi_prev = select(func.avg(SensorData.aqi)).where(
            (SensorData.location_id == location_id) & 
            (SensorData.measured_at >= time_limit_prev) &
            (SensorData.measured_at < time_limit)
        )
        res_aqi_prev = await db.execute(query_aqi_prev)
        avg_aqi_prev = res_aqi_prev.scalar() or 25.0

        aqi_diff = avg_aqi - avg_aqi_prev
        
        # Check violations trend (last 7 days vs previous 7 days)
        violation_limit_prev = datetime.now(timezone.utc) - timedelta(days=14)
        query_v_prev = select(func.count(Violation.id)).where(
            (Violation.location_id == location_id) & 
            (Violation.violation_timestamp >= violation_limit_prev) &
            (Violation.violation_timestamp < violation_limit) &
            (Violation.status != "DISMISSED")
        )
        res_v_prev = await db.execute(query_v_prev)
        violation_count_prev = res_v_prev.scalar() or 0
        prev_week_violations = violation_count_prev - violation_count

        v_diff = violation_count - prev_week_violations

        # Determine trend direction
        if aqi_diff > 5.0 or v_diff > 2:
            trend_direction = "DECLINING"
        elif aqi_diff < -5.0 or v_diff < -2:
            trend_direction = "IMPROVING"
        else:
            trend_direction = "STABLE"

        # --- 5. Risk Prediction (3-Day Forward Forecast) ---
        composite_score = int(0.35 * a_score + 0.40 * w_score + 0.25 * c_score)
        
        predicted_risk = "Low"
        if composite_score < 55 or (composite_score < 70 and trend_direction == "DECLINING"):
            predicted_risk = "High"
        elif composite_score < 75 or trend_direction == "DECLINING":
            predicted_risk = "Medium"

        return {
            "location_id": location_id,
            "location_name": loc.name,
            "composite_green_index": composite_score,
            "environmental_trend": trend_direction,
            "predicted_risk_3day": predicted_risk,
            "breakdown": {
                "air_quality_score": a_score,
                "avg_24h_aqi": round(float(avg_aqi), 2),
                "waste_compliance_score": w_score,
                "recent_violations_count": violation_count,
                "crowd_congestion_score": c_score
            }
        }

    # ----------------------------------------------------------------------------
    # 3. ROUTE COMPLIANCE MODEL (Char Dham Path composite)
    # ----------------------------------------------------------------------------
    @staticmethod
    async def calculate_route_compliance_score(db: AsyncSession, location_ids: list[int]) -> dict:
        """
        Computes the total route health index by averaging green indexes of individual sites.
        Formula:
            S_route = sum(S_location_i) / n
        """
        scores = []
        breakdown = []
        
        for loc_id in location_ids:
            score_data = await ComplianceScoringEngine.calculate_location_compliance_score(db, loc_id)
            if "error" not in score_data:
                scores.append(score_data["composite_green_index"])
                breakdown.append({
                    "location_id": loc_id,
                    "name": score_data["location_name"],
                    "score": score_data["composite_green_index"]
                })

        route_index = int(np.mean(scores)) if scores else 100
        
        return {
            "route_compliance_index": route_index,
            "locations_evaluated": len(scores),
            "route_breakdown": breakdown
        }

    @classmethod
    async def calculate_environmental_risk_scoring(cls, db: AsyncSession) -> dict:
        """
        Generates a comprehensive environmental risk scoring payload including:
        - Vehicle eco score: average eco index of all transited vehicles
        - Location eco score: green compliance index for Gaurikund (ID 1)
        - Route eco score: average green index across Rudraprayag-Chamoli loop
        - Repeat offender score: measure of recurring infractions
        - Pollution impact score: based on PM2.5, AQI, and CO2 readings
        """
        # 1. VEHICLE ECO SCORE
        # S_eco = 0.4 * S_emission + 0.3 * S_fuel + 0.3 * S_compliance
        query_vehicles = select(Vehicle)
        res_vehicles = await db.execute(query_vehicles)
        vehicles = res_vehicles.scalars().all()
        
        vehicle_scores = []
        for v in vehicles:
            # Emission standard score
            std = (v.emission_standard or "BS-VI").upper()
            if "BS-VI" in std or "BS6" in std:
                s_emission = 100
            elif "BS-V" in std or "BS5" in std:
                s_emission = 80
            elif "BS-IV" in std or "BS4" in std:
                s_emission = 70
            elif "BS-III" in std or "BS3" in std:
                s_emission = 40
            else:
                s_emission = 30
                
            # Fuel type score
            fuel = (v.fuel_type or "Petrol").lower()
            if "electric" in fuel:
                s_fuel = 100
            elif "cng" in fuel or "hybrid" in fuel:
                s_fuel = 90
            elif "petrol" in fuel or "lpg" in fuel:
                s_fuel = 70
            elif "diesel" in fuel:
                s_fuel = 50
            else:
                s_fuel = 60
                
            s_comp = v.compliance_score if v.compliance_score is not None else 100
            eco_val = int(0.4 * s_emission + 0.3 * s_fuel + 0.3 * s_comp)
            vehicle_scores.append(eco_val)
            
        avg_vehicle_eco = int(np.mean(vehicle_scores)) if vehicle_scores else 85
        
        # 2. LOCATION ECO SCORE
        loc_score_data = await cls.calculate_location_compliance_score(db, 1)
        location_eco = loc_score_data.get("composite_green_index", 85)
        
        # 3. ROUTE ECO SCORE
        route_score_data = await cls.calculate_route_compliance_score(db, [1, 2])
        route_eco = route_score_data.get("route_compliance_index", 80)
        
        # 4. REPEAT OFFENDER SCORE
        # S_repeat = min(100, count of vehicles with multiple violations * 25)
        query_offenders = select(Violation.plate_number, func.count(Violation.id)).where(
            Violation.status != "DISMISSED"
        ).group_by(Violation.plate_number)
        res_offenders = await db.execute(query_offenders)
        offenders = res_offenders.all()
        
        total_offenders = len(offenders)
        repeat_offenders = sum(1 for plate, count in offenders if count >= 2)
        
        if total_offenders > 0:
            repeat_ratio = repeat_offenders / total_offenders
            repeat_score = min(100, int(repeat_ratio * 100 + (repeat_offenders * 10)))
        else:
            repeat_score = 0
            
        # 5. POLLUTION IMPACT SCORE
        # Derived from latest SensorData
        query_sensor = select(SensorData).order_by(SensorData.measured_at.desc()).limit(1)
        res_sensor = await db.execute(query_sensor)
        latest_sensor = res_sensor.scalars().first()
        
        if latest_sensor:
            aqi = latest_sensor.aqi or 50
            pm25 = float(latest_sensor.pm25 or 15.0)
            co2 = float(latest_sensor.co2 or 400.0)
        else:
            aqi = 65
            pm25 = 22.0
            co2 = 415.0
            
        s_aqi = min(100, int((aqi / 300) * 100))
        s_pm25 = min(100, int((pm25 / 100) * 100))
        s_co2 = min(100, int((max(0, co2 - 400) / 600) * 100))
        
        pollution_impact = int(0.4 * s_aqi + 0.3 * s_pm25 + 0.3 * s_co2)
        pollution_impact = max(5, min(100, pollution_impact)) # baseline minimum of 5% impact
        
        return {
            "vehicle_eco_score": avg_vehicle_eco,
            "location_eco_score": location_eco,
            "route_eco_score": route_eco,
            "repeat_offender_score": repeat_score,
            "pollution_impact_score": pollution_impact
        }
