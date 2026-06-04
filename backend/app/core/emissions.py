# backend/app/core/emissions.py
# Production core engine for emissions footprinting and offset recommendations.

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timezone
from ..db.models import Vehicle, VehicleLog, EmissionsHistory

logger = logging.getLogger("spems.emissions")

class EmissionsCalculatorEngine:
    CORRIDOR_DISTANCE_KM = 6.0

    @classmethod
    async def calculate_emissions(cls, db: AsyncSession, save_to_history: bool = True) -> dict:
        """
        Runs calculations over active transit logs in the database.
        Computes CO2 output, particulate matter, required tree plantings, and financial offset allocations.
        """
        # 1. Total Registered Vehicles count
        total_vehicles_res = await db.execute(select(func.count(Vehicle.plate_number)))
        total_vehicles = total_vehicles_res.scalar() or 0

        # 2. Total Transit Logs count
        total_transits_res = await db.execute(select(func.count(VehicleLog.id)))
        total_transits = total_transits_res.scalar() or 0

        # 3. Query segments grouped by standard and type
        query = (
            select(
                Vehicle.emission_standard,
                Vehicle.vehicle_type,
                func.count(VehicleLog.id)
            )
            .join(Vehicle, VehicleLog.plate_number == Vehicle.plate_number)
            .group_by(Vehicle.emission_standard, Vehicle.vehicle_type)
        )
        res = await db.execute(query)
        rows = res.all()

        total_co2_grams = 0.0
        total_pm_grams = 0.0
        segments_data = []

        for standard, v_type, count in rows:
            segment_dist = count * cls.CORRIDOR_DISTANCE_KM
            
            # Formulate emission factors
            v_type_lower = v_type.lower()
            if "bus" in v_type_lower or "truck" in v_type_lower or "commercial" in v_type_lower:
                co2_factor = 750.0
                pm_factor = 0.05
            else:
                if standard == "BS-VI":
                    co2_factor = 130.0
                    pm_factor = 0.005
                else:
                    co2_factor = 160.0
                    pm_factor = 0.025
            
            co2_emitted = segment_dist * co2_factor
            pm_emitted = segment_dist * pm_factor
            
            total_co2_grams += co2_emitted
            total_pm_grams += pm_emitted

            segments_data.append({
                "vehicle_type": v_type,
                "emission_standard": standard,
                "transits_count": count,
                "co2_emitted_kg": round(co2_emitted / 1000.0, 2),
                "pm_emitted_g": round(pm_emitted, 2)
            })

        total_co2_kg = round(total_co2_grams / 1000.0, 2)
        total_pm_g = round(total_pm_grams, 2)

        # 4. Offsets & mitigation recommendations
        # 1 mature tree absorbs approx 22 kg of CO2 per year
        trees_offset_required = int(total_co2_kg / 22.0) + 1 if total_co2_kg > 0 else 0
        offset_cost_inr = float(trees_offset_required * 150)
        idle_savings_kg = round(total_co2_kg * 0.18, 2)

        payload = {
            "total_vehicles": total_vehicles,
            "total_transits": total_transits,
            "corridor_distance_km": cls.CORRIDOR_DISTANCE_KM,
            "total_co2_kg": total_co2_kg,
            "total_pm_g": total_pm_g,
            "trees_offset_required": trees_offset_required,
            "offset_cost_inr": offset_cost_inr,
            "idle_savings_kg": idle_savings_kg,
            "segments": segments_data
        }

        # Save to database log history
        if save_to_history and total_transits > 0:
            try:
                history_record = EmissionsHistory(
                    total_vehicles=total_vehicles,
                    total_transits=total_transits,
                    total_co2_kg=total_co2_kg,
                    total_pm_g=total_pm_g,
                    trees_offset=trees_offset_required,
                    offset_cost_inr=offset_cost_inr,
                    idle_savings_kg=idle_savings_kg,
                    segment_data=segments_data
                )
                db.add(history_record)
                await db.commit()
                logger.info(f"Successfully recorded emissions calculation to history database.")
            except Exception as e:
                logger.error(f"Failed to write emissions calculation log to DB: {e}")
                await db.rollback()

        return payload

    @classmethod
    async def get_emissions_history(cls, db: AsyncSession, limit: int = 50) -> list:
        """Retrieves past calculations from the database."""
        query = select(EmissionsHistory).order_by(EmissionsHistory.calculated_at.desc()).limit(limit)
        res = await db.execute(query)
        return res.scalars().all()
